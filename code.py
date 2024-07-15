import usb_midi
import busio
import board
import asyncio

# Initialize USB MIDI input and output
midi_in = usb_midi.ports[0]
midi_out_usb = usb_midi.ports[1]

# Initialize UART MIDI input and output
midi_uart = busio.UART(tx=board.GP0, rx=board.GP1, baudrate=31250)

buffer_usb_to_uart = []
buffer_uart_to_usb = []

async def read_midi_message(midi_port):
    msg = []
    while True:
        byte = midi_port.read(1)
        if byte:
            msg.append(byte[0])
            # Check for SysEx start and end
            if msg[0] == 0xF0:
                if byte[0] == 0xF7:
                    break
            else:
                # Check for standard MIDI message lengths
                if (len(msg) == 3 and msg[0] != 0xF0) or (len(msg) == 2 and (msg[0] & 0xF0) in [0xC0, 0xD0]):
                    break
        else:
            await asyncio.sleep(0)  # Yield control to the event loop
    return msg

async def process_midi():
    while True:
        # Read from USB MIDI and send to UART MIDI
        msg_usb = await read_midi_message(midi_in)
        if msg_usb:
            buffer_usb_to_uart.append(bytes(msg_usb))
        
        if buffer_usb_to_uart:
            midi_uart.write(buffer_usb_to_uart.pop(0))

        # Read from UART MIDI and send to USB MIDI
        msg_uart = await read_midi_message(midi_uart)
        if msg_uart:
            buffer_uart_to_usb.append(bytes(msg_uart))
        
        if buffer_uart_to_usb:
            midi_out_usb.write(buffer_uart_to_usb.pop(0))

        await asyncio.sleep(0)  # Yield control to the event loop

# Run the asynchronous MIDI processing loop
asyncio.run(process_midi())
