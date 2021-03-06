# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from proto import wxfetcher_pb2 as proto_dot_wxfetcher__pb2


class WxFetcherStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.FetchURL = channel.unary_unary(
        '/WxFetcher/FetchURL',
        request_serializer=proto_dot_wxfetcher__pb2.FetchURLRequest.SerializeToString,
        response_deserializer=proto_dot_wxfetcher__pb2.FetchURLResponse.FromString,
        )


class WxFetcherServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def FetchURL(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_WxFetcherServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'FetchURL': grpc.unary_unary_rpc_method_handler(
          servicer.FetchURL,
          request_deserializer=proto_dot_wxfetcher__pb2.FetchURLRequest.FromString,
          response_serializer=proto_dot_wxfetcher__pb2.FetchURLResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'WxFetcher', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
