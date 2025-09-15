"""
Test script for fragmented message handling
This script demonstrates how the message buffer service handles fragmented messages
from Evolution API (WhatsApp)
"""

import asyncio
import logging
from message_buffer_service import message_buffer_service
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_numbered_fragments():
    """Test numbered fragments like [1/3], [2/3], [3/3]"""
    print("\n=== Testing Numbered Fragments ===")
    
    tenant_id = "test_tenant"
    whatsapp_number = "5511999999999"
    conversation_id = "test_conversation_1"
    
    # Simulate fragmented message with numbered indicators
    fragments = [
        "[1/3] Esta é a primeira parte da mensagem que foi",
        "[2/3] dividida em três partes pelo WhatsApp",
        "[3/3] e precisa ser reconstituída corretamente."
    ]
    
    complete_message = None
    for i, fragment in enumerate(fragments):
        print(f"Sending fragment {i+1}: {fragment}")
        result = await message_buffer_service.process_message(
            tenant_id=tenant_id,
            whatsapp_number=whatsapp_number,
            conversation_id=conversation_id,
            message_content=fragment,
            message_id=f"msg_{i+1}"
        )
        
        if result:
            complete_message = result
            print(f"✅ Complete message received: {complete_message}")
            break
        else:
            print(f"⏳ Fragment buffered, waiting for more...")
    
    return complete_message

async def test_continuation_fragments():
    """Test continuation fragments ending with ... or …"""
    print("\n=== Testing Continuation Fragments ===")
    
    tenant_id = "test_tenant"
    whatsapp_number = "5511888888888"
    conversation_id = "test_conversation_2"
    
    # Simulate fragmented message with continuation indicators
    fragments = [
        "Esta mensagem foi dividida automaticamente pelo WhatsApp...",
        "e precisa ser reconstituída para formar uma mensagem completa...",
        "sem perder nenhuma informação importante."
    ]
    
    complete_message = None
    for i, fragment in enumerate(fragments):
        print(f"Sending fragment {i+1}: {fragment}")
        result = await message_buffer_service.process_message(
            tenant_id=tenant_id,
            whatsapp_number=whatsapp_number,
            conversation_id=conversation_id,
            message_content=fragment,
            message_id=f"msg_{i+1}"
        )
        
        if result:
            complete_message = result
            print(f"✅ Complete message received: {complete_message}")
            break
        else:
            print(f"⏳ Fragment buffered, waiting for more...")
    
    return complete_message

async def test_length_split_fragments():
    """Test fragments split by length (WhatsApp automatic splitting)"""
    print("\n=== Testing Length-Split Fragments ===")
    
    tenant_id = "test_tenant"
    whatsapp_number = "5511777777777"
    conversation_id = "test_conversation_3"
    
    # Simulate very long message that gets split
    long_message = "Esta é uma mensagem muito longa que excede o limite de caracteres do WhatsApp e por isso é automaticamente dividida em múltiplas partes. O sistema precisa detectar isso e reconstituir a mensagem original corretamente."
    
    print(f"Sending long message: {long_message}")
    result = await message_buffer_service.process_message(
        tenant_id=tenant_id,
        whatsapp_number=whatsapp_number,
        conversation_id=conversation_id,
        message_content=long_message,
        message_id="long_msg_1"
    )
    
    if result:
        print(f"✅ Complete message received: {result}")
    else:
        print(f"⏳ Message buffered as potential fragment")
    
    return result

async def test_mixed_scenarios():
    """Test mixed scenarios with different fragment types"""
    print("\n=== Testing Mixed Scenarios ===")
    
    tenant_id = "test_tenant"
    whatsapp_number = "5511666666666"
    conversation_id = "test_conversation_4"
    
    # Test regular message (not fragmented)
    regular_message = "Esta é uma mensagem normal que não precisa de buffer."
    print(f"Sending regular message: {regular_message}")
    
    result = await message_buffer_service.process_message(
        tenant_id=tenant_id,
        whatsapp_number=whatsapp_number,
        conversation_id=conversation_id,
        message_content=regular_message,
        message_id="regular_msg"
    )
    
    if result:
        print(f"✅ Regular message processed: {result}")
    
    # Test incomplete numbered fragment
    incomplete_fragment = "[1/3] Esta mensagem não será completada"
    print(f"Sending incomplete fragment: {incomplete_fragment}")
    
    result = await message_buffer_service.process_message(
        tenant_id=tenant_id,
        whatsapp_number=whatsapp_number,
        conversation_id=conversation_id,
        message_content=incomplete_fragment,
        message_id="incomplete_msg"
    )
    
    if result:
        print(f"✅ Fragment completed: {result}")
    else:
        print(f"⏳ Fragment buffered, waiting for completion...")
    
    return result

async def test_buffer_status():
    """Test buffer status monitoring"""
    print("\n=== Testing Buffer Status ===")
    
    active_count = message_buffer_service.get_active_buffers_count()
    buffer_info = message_buffer_service.get_active_buffers_info()
    
    print(f"Active buffers count: {active_count}")
    print(f"Buffer details: {buffer_info}")
    
    return active_count, buffer_info

async def test_force_completion():
    """Test forcing completion of fragmented messages"""
    print("\n=== Testing Force Completion ===")
    
    tenant_id = "test_tenant"
    whatsapp_number = "5511555555555"
    conversation_id = "test_conversation_5"
    
    # Create an incomplete buffer
    await message_buffer_service.process_message(
        tenant_id=tenant_id,
        whatsapp_number=whatsapp_number,
        conversation_id=conversation_id,
        message_content="[1/3] Fragmento incompleto",
        message_id="incomplete_1"
    )
    
    print("Created incomplete buffer")
    
    # Force completion
    complete_message = await message_buffer_service.force_complete_message(
        tenant_id, whatsapp_number, conversation_id
    )
    
    if complete_message:
        print(f"✅ Forced completion successful: {complete_message}")
    else:
        print("❌ No buffer found to complete")
    
    return complete_message

async def main():
    """Run all tests"""
    print("🧪 Starting Fragmented Message Tests")
    print("=" * 50)
    
    try:
        # Test different fragment types
        await test_numbered_fragments()
        await test_continuation_fragments()
        await test_length_split_fragments()
        await test_mixed_scenarios()
        
        # Test monitoring
        await test_buffer_status()
        
        # Test force completion
        await test_force_completion()
        
        # Final status
        print("\n=== Final Buffer Status ===")
        await test_buffer_status()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
