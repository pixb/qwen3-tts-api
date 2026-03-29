import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';
}

class DioClient {
  // Change to your computer's IP address when running on mobile device
  static const String baseUrl = 'http://localhost:8001';
  // For mobile: static const String baseUrl = 'http://192.168.x.x:8001';

  late final Dio _dio;

  DioClient({String? authToken}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
        headers: {
          'Content-Type': 'application/json',
          'Accept': '*/*',
          if (authToken != null) 'Authorization': 'Bearer $authToken',
        },
      ),
    );

    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }

  Dio get dio => _dio;

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.get<T>(path, queryParameters: queryParameters);
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    Duration? timeout,
  }) async {
    Options mergedOptions = options ?? Options();
    if (timeout != null) {
      mergedOptions = mergedOptions.copyWith(
        connectTimeout: timeout,
        receiveTimeout: timeout,
      );
    }
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: mergedOptions,
    );
  }

  Future<Response<T>> postForm<T>(
    String path, {
    required Map<String, dynamic> data,
    Duration? timeout,
  }) async {
    Options options = Options(
      headers: {'Content-Type': 'multipart/form-data'},
    );
    if (timeout != null) {
      options = options.copyWith(
        connectTimeout: timeout,
        receiveTimeout: timeout,
      );
    }
    return _dio.post<T>(
      path,
      data: FormData.fromMap(data),
      options: options,
    );
  }

  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.delete<T>(path, data: data, queryParameters: queryParameters);
  }

  Future<Response<T>> postMultipart<T>(
    String path, {
    required FormData formData,
    ResponseType? responseType,
    Duration? timeout,
  }) async {
    Options options = Options(
      headers: {'Content-Type': 'multipart/form-data'},
      responseType: responseType,
    );
    if (timeout != null) {
      options = options.copyWith(
        connectTimeout: timeout,
        receiveTimeout: timeout,
      );
    }
    return _dio.post<T>(
      path,
      data: formData,
      options: options,
    );
  }
}

final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient();
});

final dioProvider = Provider<Dio>((ref) {
  return ref.watch(dioClientProvider).dio;
});
