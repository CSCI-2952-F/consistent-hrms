# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: discovery.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='discovery.proto',
  package='',
  syntax='proto3',
  serialized_options=b'Z\004main',
  serialized_pb=b'\n\x0f\x64iscovery.proto\"<\n\x08Hospital\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x16\n\x0eregisteredTime\x18\x03 \x01(\x03\"B\n\x05Lease\x12\n\n\x02ID\x18\x01 \x01(\x03\x12\x0b\n\x03TTL\x18\x02 \x01(\x03\x12\x12\n\ngrantedTTL\x18\x03 \x01(\x03\x12\x0c\n\x04keys\x18\x04 \x03(\x0c\"\r\n\x0bInfoRequest\"B\n\x0cInfoResponse\x12\x1b\n\x08hospital\x18\x01 \x01(\x0b\x32\t.Hospital\x12\x15\n\x05lease\x18\x02 \x01(\x0b\x32\x06.Lease\"\r\n\x0bListRequest\",\n\x0cListResponse\x12\x1c\n\thospitals\x18\x01 \x03(\x0b\x32\t.Hospital2m\n\x11HospitalDiscovery\x12(\n\x07GetInfo\x12\x0c.InfoRequest\x1a\r.InfoResponse\"\x00\x12.\n\rListHospitals\x12\x0c.ListRequest\x1a\r.ListResponse\"\x00\x42\x06Z\x04mainb\x06proto3'
)




_HOSPITAL = _descriptor.Descriptor(
  name='Hospital',
  full_name='Hospital',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='Hospital.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='name', full_name='Hospital.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='registeredTime', full_name='Hospital.registeredTime', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=19,
  serialized_end=79,
)


_LEASE = _descriptor.Descriptor(
  name='Lease',
  full_name='Lease',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ID', full_name='Lease.ID', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='TTL', full_name='Lease.TTL', index=1,
      number=2, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='grantedTTL', full_name='Lease.grantedTTL', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='keys', full_name='Lease.keys', index=3,
      number=4, type=12, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=81,
  serialized_end=147,
)


_INFOREQUEST = _descriptor.Descriptor(
  name='InfoRequest',
  full_name='InfoRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=149,
  serialized_end=162,
)


_INFORESPONSE = _descriptor.Descriptor(
  name='InfoResponse',
  full_name='InfoResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hospital', full_name='InfoResponse.hospital', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lease', full_name='InfoResponse.lease', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=164,
  serialized_end=230,
)


_LISTREQUEST = _descriptor.Descriptor(
  name='ListRequest',
  full_name='ListRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=232,
  serialized_end=245,
)


_LISTRESPONSE = _descriptor.Descriptor(
  name='ListResponse',
  full_name='ListResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hospitals', full_name='ListResponse.hospitals', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=247,
  serialized_end=291,
)

_INFORESPONSE.fields_by_name['hospital'].message_type = _HOSPITAL
_INFORESPONSE.fields_by_name['lease'].message_type = _LEASE
_LISTRESPONSE.fields_by_name['hospitals'].message_type = _HOSPITAL
DESCRIPTOR.message_types_by_name['Hospital'] = _HOSPITAL
DESCRIPTOR.message_types_by_name['Lease'] = _LEASE
DESCRIPTOR.message_types_by_name['InfoRequest'] = _INFOREQUEST
DESCRIPTOR.message_types_by_name['InfoResponse'] = _INFORESPONSE
DESCRIPTOR.message_types_by_name['ListRequest'] = _LISTREQUEST
DESCRIPTOR.message_types_by_name['ListResponse'] = _LISTRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Hospital = _reflection.GeneratedProtocolMessageType('Hospital', (_message.Message,), {
  'DESCRIPTOR' : _HOSPITAL,
  '__module__' : 'discovery_pb2'
  # @@protoc_insertion_point(class_scope:Hospital)
  })
_sym_db.RegisterMessage(Hospital)

Lease = _reflection.GeneratedProtocolMessageType('Lease', (_message.Message,), {
  'DESCRIPTOR' : _LEASE,
  '__module__' : 'discovery_pb2'
  # @@protoc_insertion_point(class_scope:Lease)
  })
_sym_db.RegisterMessage(Lease)

InfoRequest = _reflection.GeneratedProtocolMessageType('InfoRequest', (_message.Message,), {
  'DESCRIPTOR' : _INFOREQUEST,
  '__module__' : 'discovery_pb2'
  # @@protoc_insertion_point(class_scope:InfoRequest)
  })
_sym_db.RegisterMessage(InfoRequest)

InfoResponse = _reflection.GeneratedProtocolMessageType('InfoResponse', (_message.Message,), {
  'DESCRIPTOR' : _INFORESPONSE,
  '__module__' : 'discovery_pb2'
  # @@protoc_insertion_point(class_scope:InfoResponse)
  })
_sym_db.RegisterMessage(InfoResponse)

ListRequest = _reflection.GeneratedProtocolMessageType('ListRequest', (_message.Message,), {
  'DESCRIPTOR' : _LISTREQUEST,
  '__module__' : 'discovery_pb2'
  # @@protoc_insertion_point(class_scope:ListRequest)
  })
_sym_db.RegisterMessage(ListRequest)

ListResponse = _reflection.GeneratedProtocolMessageType('ListResponse', (_message.Message,), {
  'DESCRIPTOR' : _LISTRESPONSE,
  '__module__' : 'discovery_pb2'
  # @@protoc_insertion_point(class_scope:ListResponse)
  })
_sym_db.RegisterMessage(ListResponse)


DESCRIPTOR._options = None

_HOSPITALDISCOVERY = _descriptor.ServiceDescriptor(
  name='HospitalDiscovery',
  full_name='HospitalDiscovery',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=293,
  serialized_end=402,
  methods=[
  _descriptor.MethodDescriptor(
    name='GetInfo',
    full_name='HospitalDiscovery.GetInfo',
    index=0,
    containing_service=None,
    input_type=_INFOREQUEST,
    output_type=_INFORESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ListHospitals',
    full_name='HospitalDiscovery.ListHospitals',
    index=1,
    containing_service=None,
    input_type=_LISTREQUEST,
    output_type=_LISTRESPONSE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_HOSPITALDISCOVERY)

DESCRIPTOR.services_by_name['HospitalDiscovery'] = _HOSPITALDISCOVERY

# @@protoc_insertion_point(module_scope)
