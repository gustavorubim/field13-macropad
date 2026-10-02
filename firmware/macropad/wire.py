"""ARC13/2 authenticated LAN protocol; integrity/authentication, NOT encryption.
Fresh host challenge per session + strict sequence numbers reject report replay.
"""
import hashlib
import binascii
import json

MAX_PACKET = 1536

def sha(value):
    result = hashlib.new('sha256')
    result.update(value)
    return result.digest()

def mac(key, body):
    if len(key) > 64:
        key = sha(key)
    key = key + b'\x00' * (64 - len(key))
    return binascii.hexlify(sha(bytes(x ^ 0x5c for x in key) +
                               sha(bytes(x ^ 0x36 for x in key) + body)))

def equal(left, right):
    if len(left) != len(right):
        return False
    different = 0
    for left_byte, right_byte in zip(left, right):
        different |= left_byte ^ right_byte
    return different == 0

def nonce_valid(value):
    return len(value) == 32 and all(x in b'0123456789abcdef' for x in value)

def signed(key, body):
    return body + b'|' + mac(key, body)

def checked(key, packet):
    if not 1 <= len(packet) <= MAX_PACKET:
        raise ValueError('Packet size')
    fields = packet.split(b'|')
    body = b'|'.join(fields[:-1])
    if len(fields) < 3 or not equal(mac(key, body), fields[-1]):
        raise ValueError('Authentication')
    return fields[:-1]

def hello(key, boot):
    if not nonce_valid(boot):
        raise ValueError('Boot nonce')
    return signed(key, b'ARC13/2H|' + boot)

def parse_hello(key, packet):
    fields = checked(key, packet)
    if len(fields) != 2 or fields[0] != b'ARC13/2H' or not nonce_valid(fields[1]):
        raise ValueError('Hello')
    return fields[1]

def challenge(key, boot, session):
    if not nonce_valid(boot) or not nonce_valid(session):
        raise ValueError('Nonce')
    return signed(key, b'ARC13/2C|' + boot + b'|' + session)

def parse_challenge(key, boot, packet):
    fields = checked(key, packet)
    if (len(fields) != 3 or fields[0] != b'ARC13/2C' or fields[1] != boot
            or not nonce_valid(fields[2])):
        raise ValueError('Challenge')
    return fields[2]

def pack(key, session, sequence, report, event=None):
    if not nonce_valid(session) or type(sequence) is not int or not 0 <= sequence < 2**53:
        raise ValueError('Session/sequence')
    if len(report) != 8 or report[1] != 0:
        raise ValueError('Keyboard report')
    extra = binascii.hexlify(json.dumps(event or {}).encode('utf-8'))
    body = b'ARC13/2R|' + session + b'|' + str(sequence).encode() + b'|' + binascii.hexlify(report) + b'|' + extra
    packet = signed(key, body)
    if len(packet) > MAX_PACKET:
        raise ValueError('Packet size')
    return packet

def unpack(key, session, last_sequence, packet):
    fields = checked(key, packet)
    if len(fields) != 5 or fields[0] != b'ARC13/2R' or fields[1] != session:
        raise ValueError('Protocol/session')
    sequence = int(fields[2])
    report = binascii.unhexlify(fields[3])
    event = json.loads(binascii.unhexlify(fields[4]).decode('utf-8'))
    if (not last_sequence < sequence < 2**53 or len(report) != 8 or report[1] != 0
            or not isinstance(event, dict)):
        raise ValueError('Sequence/report')
    return sequence, report, event
