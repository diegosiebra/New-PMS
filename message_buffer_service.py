import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from models import FragmentedMessage, MessageFragment
import re

logger = logging.getLogger(__name__)

class MessageBufferService:
    """Service to handle fragmented messages from Evolution API"""
    
    def __init__(self):
        self.active_buffers: Dict[str, FragmentedMessage] = {}
        self.cleanup_task = None
        self.start_cleanup_task()
    
    def start_cleanup_task(self):
        """Start background task to clean up expired buffers"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_buffers())
    
    async def _cleanup_expired_buffers(self):
        """Background task to clean up expired message buffers"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                current_time = datetime.now()
                expired_keys = []
                
                for buffer_key, buffer in self.active_buffers.items():
                    if current_time - buffer.timestamp > timedelta(seconds=buffer.timeout_seconds):
                        expired_keys.append(buffer_key)
                        logger.warning(f"Expired fragmented message buffer: {buffer_key}")
                
                for key in expired_keys:
                    del self.active_buffers[key]
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def _detect_fragmented_message(self, message_content: str) -> Optional[Dict[str, any]]:
        """
        Detect if a message is fragmented based on common patterns
        Returns dict with fragment info or None if not fragmented
        """
        # Pattern 1: Messages ending with "..." or "…" (continuation)
        if message_content.endswith(('...', '…')):
            return {
                'type': 'continuation',
                'is_last': False,
                'fragment_number': None
            }
        
        # Pattern 2: Messages starting with "..." or "…" (continuation from previous)
        if message_content.startswith(('...', '…')):
            return {
                'type': 'continuation',
                'is_last': False,
                'fragment_number': None
            }
        
        # Pattern 3: Messages with fragment indicators like [1/3], [2/3], etc.
        fragment_pattern = r'\[(\d+)/(\d+)\]'
        match = re.search(fragment_pattern, message_content)
        if match:
            current_frag = int(match.group(1))
            total_frags = int(match.group(2))
            return {
                'type': 'numbered',
                'fragment_number': current_frag,
                'total_fragments': total_frags,
                'is_last': current_frag == total_frags
            }
        
        # Pattern 4: Very long messages that might be split by WhatsApp
        if len(message_content) > 1000:  # WhatsApp typically splits at ~1000 chars
            return {
                'type': 'length_split',
                'is_last': False,
                'fragment_number': None
            }
        
        return None
    
    def _create_buffer_key(self, tenant_id: str, whatsapp_number: str, conversation_id: str) -> str:
        """Create unique key for message buffer"""
        return f"{tenant_id}:{whatsapp_number}:{conversation_id}"
    
    async def process_message(self, tenant_id: str, whatsapp_number: str, conversation_id: str, 
                            message_content: str, message_id: str) -> Optional[str]:
        """
        Process incoming message and return complete message if ready, None if still buffering
        """
        try:
            buffer_key = self._create_buffer_key(tenant_id, whatsapp_number, conversation_id)
            
            # Check if this is a fragmented message
            fragment_info = self._detect_fragmented_message(message_content)
            
            if fragment_info is None:
                # Not a fragmented message, check if we have an active buffer
                if buffer_key in self.active_buffers:
                    # Complete the current buffer with this message
                    buffer = self.active_buffers[buffer_key]
                    buffer.fragments.append(message_content)
                    buffer.is_complete = True
                    buffer.assembled_content = ' '.join(buffer.fragments)
                    
                    # Remove from active buffers
                    del self.active_buffers[buffer_key]
                    
                    logger.info(f"Completed fragmented message for {buffer_key}")
                    return buffer.assembled_content
                else:
                    # Regular message, return as is
                    return message_content
            
            # Handle fragmented message
            if fragment_info['type'] == 'numbered':
                return await self._handle_numbered_fragment(
                    buffer_key, tenant_id, whatsapp_number, conversation_id,
                    message_content, message_id, fragment_info
                )
            elif fragment_info['type'] == 'continuation':
                return await self._handle_continuation_fragment(
                    buffer_key, tenant_id, whatsapp_number, conversation_id,
                    message_content, message_id, fragment_info
                )
            elif fragment_info['type'] == 'length_split':
                return await self._handle_length_split_fragment(
                    buffer_key, tenant_id, whatsapp_number, conversation_id,
                    message_content, message_id, fragment_info
                )
            
            return message_content
            
        except Exception as e:
            logger.error(f"Error processing fragmented message: {e}")
            return message_content
    
    async def _handle_numbered_fragment(self, buffer_key: str, tenant_id: str, whatsapp_number: str,
                                      conversation_id: str, message_content: str, message_id: str,
                                      fragment_info: Dict) -> Optional[str]:
        """Handle numbered fragments like [1/3], [2/3], etc."""
        
        fragment_number = fragment_info['fragment_number']
        total_fragments = fragment_info['total_fragments']
        is_last = fragment_info['is_last']
        
        # Remove fragment indicator from content
        clean_content = re.sub(r'\[\d+/\d+\]', '', message_content).strip()
        
        if buffer_key not in self.active_buffers:
            # Create new buffer
            buffer = FragmentedMessage(
                message_id=message_id,
                tenant_id=tenant_id,
                whatsapp_number=whatsapp_number,
                conversation_id=conversation_id,
                fragments=[clean_content],
                total_fragments=total_fragments,
                current_fragment=fragment_number,
                timestamp=datetime.now()
            )
            self.active_buffers[buffer_key] = buffer
        else:
            # Add to existing buffer
            buffer = self.active_buffers[buffer_key]
            buffer.fragments.append(clean_content)
            buffer.current_fragment = fragment_number
        
        if is_last or len(buffer.fragments) >= total_fragments:
            # Message is complete
            buffer.is_complete = True
            buffer.assembled_content = ' '.join(buffer.fragments)
            del self.active_buffers[buffer_key]
            
            logger.info(f"Completed numbered fragmented message for {buffer_key}")
            return buffer.assembled_content
        
        logger.info(f"Buffering numbered fragment {fragment_number}/{total_fragments} for {buffer_key}")
        return None
    
    async def _handle_continuation_fragment(self, buffer_key: str, tenant_id: str, whatsapp_number: str,
                                          conversation_id: str, message_content: str, message_id: str,
                                          fragment_info: Dict) -> Optional[str]:
        """Handle continuation fragments ending with ... or …"""
        
        # Remove continuation indicators
        clean_content = message_content.rstrip('…...').strip()
        
        if buffer_key not in self.active_buffers:
            # Create new buffer
            buffer = FragmentedMessage(
                message_id=message_id,
                tenant_id=tenant_id,
                whatsapp_number=whatsapp_number,
                conversation_id=conversation_id,
                fragments=[clean_content],
                timestamp=datetime.now()
            )
            self.active_buffers[buffer_key] = buffer
        else:
            # Add to existing buffer
            buffer = self.active_buffers[buffer_key]
            buffer.fragments.append(clean_content)
        
        logger.info(f"Buffering continuation fragment for {buffer_key}")
        return None
    
    async def _handle_length_split_fragment(self, buffer_key: str, tenant_id: str, whatsapp_number: str,
                                          conversation_id: str, message_content: str, message_id: str,
                                          fragment_info: Dict) -> Optional[str]:
        """Handle fragments split by length (WhatsApp automatic splitting)"""
        
        if buffer_key not in self.active_buffers:
            # Create new buffer
            buffer = FragmentedMessage(
                message_id=message_id,
                tenant_id=tenant_id,
                whatsapp_number=whatsapp_number,
                conversation_id=conversation_id,
                fragments=[message_content],
                timestamp=datetime.now()
            )
            self.active_buffers[buffer_key] = buffer
        else:
            # Add to existing buffer
            buffer = self.active_buffers[buffer_key]
            buffer.fragments.append(message_content)
        
        logger.info(f"Buffering length-split fragment for {buffer_key}")
        return None
    
    async def force_complete_message(self, tenant_id: str, whatsapp_number: str, conversation_id: str) -> Optional[str]:
        """Force complete any pending fragmented message (useful for timeouts)"""
        buffer_key = self._create_buffer_key(tenant_id, whatsapp_number, conversation_id)
        
        if buffer_key in self.active_buffers:
            buffer = self.active_buffers[buffer_key]
            buffer.is_complete = True
            buffer.assembled_content = ' '.join(buffer.fragments)
            del self.active_buffers[buffer_key]
            
            logger.info(f"Forced completion of fragmented message for {buffer_key}")
            return buffer.assembled_content
        
        return None
    
    def get_active_buffers_count(self) -> int:
        """Get count of active message buffers"""
        return len(self.active_buffers)
    
    def get_active_buffers_info(self) -> List[Dict]:
        """Get information about active buffers for debugging"""
        return [
            {
                'buffer_key': key,
                'fragments_count': len(buffer.fragments),
                'total_fragments': buffer.total_fragments,
                'age_seconds': (datetime.now() - buffer.timestamp).total_seconds(),
                'is_complete': buffer.is_complete
            }
            for key, buffer in self.active_buffers.items()
        ]

# Global message buffer service instance
message_buffer_service = MessageBufferService()
