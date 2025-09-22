import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from models import FragmentedMessage, MessageFragment
import re

logger = logging.getLogger(__name__)

# Buffer timing configuration
BUFFER_COMPLETION_TIME = 3.0  # Seconds to wait before completing sequence buffer
MESSAGE_GROUPING_WINDOW = 5.0  # Seconds window to group sequential messages
BUFFER_TIMEOUT_SECONDS = 10  # Maximum time a buffer can stay active
CLEANUP_CHECK_INTERVAL = 2  # Seconds between cleanup task checks

class MessageBufferService:
    """Service to handle fragmented messages from Evolution API"""
    
    def __init__(self):
        self.active_buffers: Dict[str, FragmentedMessage] = {}
        self.cleanup_task = None
        self._cleanup_started = False
        self.completion_callbacks: Dict[str, callable] = {}
    
    def start_cleanup_task(self):
        """Start background task to clean up expired buffers"""
        if not self._cleanup_started:
            try:
                loop = asyncio.get_running_loop()
                if self.cleanup_task is None or self.cleanup_task.done():
                    self.cleanup_task = asyncio.create_task(self._cleanup_expired_buffers())
                    self._cleanup_started = True
            except RuntimeError:
                # No event loop running, cleanup will be started when first message is processed
                pass
    
    async def _cleanup_expired_buffers(self):
        """Background task to clean up expired message buffers and complete sequence buffers"""
        while True:
            try:
                await asyncio.sleep(CLEANUP_CHECK_INTERVAL)  # Check every N seconds
                current_time = datetime.now()
                expired_keys = []
                completed_sequence_keys = []
                
                for buffer_key, buffer in self.active_buffers.items():
                    time_diff = (current_time - buffer.timestamp).total_seconds()
                    
                    # Check for expired buffers
                    if time_diff > buffer.timeout_seconds:
                        expired_keys.append(buffer_key)
                        logger.warning(f"Expired fragmented message buffer: {buffer_key}")
                    
                    # Check for sequence buffers that should be completed
                    elif ':sequence' in buffer_key and time_diff >= BUFFER_COMPLETION_TIME and not buffer.is_complete:
                        buffer.is_complete = True
                        buffer.assembled_content = ' '.join(buffer.fragments)
                        completed_sequence_keys.append(buffer_key)
                        logger.info(f"Completed sequence buffer due to timeout: {buffer_key}")
                
                # Remove expired buffers
                for key in expired_keys:
                    del self.active_buffers[key]
                
                # Process completed sequence buffers
                for key in completed_sequence_keys:
                    if key in self.completion_callbacks:
                        try:
                            callback = self.completion_callbacks[key]
                            await callback(key, self.active_buffers[key])
                            logger.info(f"Called completion callback for {key}")
                        except Exception as e:
                            logger.error(f"Error calling completion callback for {key}: {e}")
                    
                    # Remove the completed buffer
                    del self.active_buffers[key]
                    if key in self.completion_callbacks:
                        del self.completion_callbacks[key]
                    
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
    
    def _create_sequence_buffer_key(self, tenant_id: str, whatsapp_number: str) -> str:
        """Create key for sequential message buffering (without conversation_id)"""
        return f"{tenant_id}:{whatsapp_number}:sequence"
    
    def register_completion_callback(self, buffer_key: str, callback: callable):
        """Register a callback to be called when a buffer is completed"""
        self.completion_callbacks[buffer_key] = callback
        logger.info(f"Registered completion callback for {buffer_key}")
    
    async def process_message(self, tenant_id: str, whatsapp_number: str, conversation_id: str, 
                            message_content: str, message_id: str) -> Optional[str]:
        """
        Process incoming message and return complete message if ready, None if still buffering
        """
        try:
            # Start cleanup task if not already started
            self.start_cleanup_task()
            
            buffer_key = self._create_buffer_key(tenant_id, whatsapp_number, conversation_id)
            sequence_key = self._create_sequence_buffer_key(tenant_id, whatsapp_number)
            
            # Note: Completed buffers are handled by the cleanup task and callbacks
            # No need to check for completed buffers here as it interferes with new messages
            
            # Check if this is a fragmented message
            fragment_info = self._detect_fragmented_message(message_content)
            
            if fragment_info is None:
                # Not a fragmented message, check for sequential buffering
                return await self._handle_sequential_message(
                    tenant_id, whatsapp_number, conversation_id, message_content, message_id, 
                    buffer_key, sequence_key
                )
            
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
    
    async def _handle_sequential_message(self, tenant_id: str, whatsapp_number: str, 
                                       conversation_id: str, message_content: str, message_id: str,
                                       buffer_key: str, sequence_key: str) -> Optional[str]:
        """Handle sequential messages that might be part of a rapid conversation"""
        try:
            current_time = datetime.now()
            
            # Check if we have an active sequence buffer
            if sequence_key in self.active_buffers:
                buffer = self.active_buffers[sequence_key]
                time_diff = (current_time - buffer.timestamp).total_seconds()
                
                # If message arrives within the grouping window, add to buffer
                if time_diff <= MESSAGE_GROUPING_WINDOW:
                    buffer.fragments.append(message_content)
                    buffer.timestamp = current_time  # Update timestamp
                    
                    logger.info(f"Added message to sequence buffer for {sequence_key} (time diff: {time_diff:.2f}s)")
                    return None
                else:
                    # Time gap too large, complete the existing buffer and process new message immediately
                    complete_message = ' '.join(buffer.fragments)
                    del self.active_buffers[sequence_key]
                    
                    logger.info(f"Completed sequence buffer due to time gap for {sequence_key}")
                    
                    # Process the new message immediately instead of buffering it
                    logger.info(f"Processing new message immediately due to time gap: {message_content}")
                    return message_content
            else:
                # No active sequence buffer, start a new one
                await self._start_new_sequence_buffer(sequence_key, tenant_id, whatsapp_number, 
                                                    conversation_id, message_content, message_id)
                return None
                
        except Exception as e:
            logger.error(f"Error handling sequential message: {e}")
            return message_content
    
    async def _start_new_sequence_buffer(self, sequence_key: str, tenant_id: str, whatsapp_number: str,
                                       conversation_id: str, message_content: str, message_id: str):
        """Start a new sequence buffer for rapid messages"""
        buffer = FragmentedMessage(
            message_id=message_id,
            tenant_id=tenant_id,
            whatsapp_number=whatsapp_number,
            conversation_id=conversation_id,
            fragments=[message_content],
            timestamp=datetime.now(),
            timeout_seconds=BUFFER_TIMEOUT_SECONDS  # Timeout for sequence buffers
        )
        self.active_buffers[sequence_key] = buffer
        
        logger.info(f"Started new sequence buffer for {sequence_key}")
        
        # Register completion callback
        async def completion_callback(buffer_key: str, completed_buffer: FragmentedMessage):
            """Callback to process completed sequence buffer"""
            try:
                from webhook_service import webhook_service
                
                complete_message = completed_buffer.assembled_content
                logger.info(f"Processing completed sequence buffer: {complete_message}")
                
                # Process the complete message with agent manager
                response = await webhook_service.agent_manager.process_message(
                    tenant_id=tenant_id,
                    message=complete_message,
                    whatsapp_number=whatsapp_number,
                    conversation_id=whatsapp_number  # Use whatsapp_number as conversation_id for consistent memory
                )
                
                logger.info(f"Agent response for completed buffer: {response}")
                
                # Send response back via EvolutionAPI
                if response.get("success"):
                    await webhook_service.send_response(tenant_id, whatsapp_number, response["message"])
                
                # Log the conversation
                await webhook_service.log_conversation(tenant_id, whatsapp_number, complete_message, response.get("message", ""), False)
                
            except Exception as e:
                logger.error(f"Error in completion callback: {e}")
        
        self.register_completion_callback(sequence_key, completion_callback)
    
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
    
    async def force_complete_sequence_buffer(self, tenant_id: str, whatsapp_number: str) -> Optional[str]:
        """Force complete any pending sequence buffer (useful for timeouts)"""
        sequence_key = self._create_sequence_buffer_key(tenant_id, whatsapp_number)
        
        if sequence_key in self.active_buffers:
            buffer = self.active_buffers[sequence_key]
            buffer.is_complete = True
            buffer.assembled_content = ' '.join(buffer.fragments)
            del self.active_buffers[sequence_key]
            
            logger.info(f"Forced completion of sequence buffer for {sequence_key}")
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
                'buffer_type': 'sequence' if ':sequence' in key else 'fragmented',
                'fragments_count': len(buffer.fragments),
                'total_fragments': buffer.total_fragments,
                'age_seconds': (datetime.now() - buffer.timestamp).total_seconds(),
                'is_complete': buffer.is_complete,
                'fragments_preview': buffer.fragments[:3] if buffer.fragments else []
            }
            for key, buffer in self.active_buffers.items()
        ]

# Global message buffer service instance
message_buffer_service = MessageBufferService()
