import 'package:dio/dio.dart';
import '../models/audio_models.dart';
import '../providers/api_provider.dart';

class ApiService {
  final DioClient _client;

  ApiService({DioClient? client}) : _client = client ?? DioClient();

  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await _client.get('/health');
      return response.data;
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<List<String>> getLanguages() async {
    try {
      final response = await _client.get('/languages');
      if (response.statusCode == 200) {
        return List<String>.from(response.data['languages']);
      }
      return [];
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<String> generateCustomVoice({
    required String text,
    required String speaker,
    double exaggeration = 0.5,
    double temperature = 0.8,
    double speedRate = 1.0,
    String? instruct,
  }) async {
    try {
      final response = await _client.postForm(
        '/tts/custom',
        data: {
          'text': text,
          'speaker': speaker,
          'exaggeration': exaggeration,
          'temperature': temperature,
          'speed_rate': speedRate,
          if (instruct != null) 'instruct': instruct,
        },
      );
      return response.statusCode == 200 ? 'success' : 'failed';
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<String> generateVoiceDesign({
    required String text,
    required String instruct,
    double exaggeration = 0.5,
    double temperature = 0.8,
    double speedRate = 1.0,
  }) async {
    try {
      final response = await _client.postForm(
        '/tts/design',
        data: {
          'text': text,
          'instruct': instruct,
          'exaggeration': exaggeration,
          'temperature': temperature,
          'speed_rate': speedRate,
        },
      );
      return response.statusCode == 200 ? 'success' : 'failed';
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<String> generateWithReference({
    required String text,
    int? referenceId,
    String? referenceName,
    double? exaggeration,
    double? temperature,
    double? speedRate,
    String? instruct,
  }) async {
    try {
      final response = await _client.postForm(
        '/tts/generate',
        data: {
          'text': text,
          if (referenceId != null) 'reference_id': referenceId,
          if (referenceName != null) 'reference_name': referenceName,
          if (exaggeration != null) 'exaggeration': exaggeration,
          if (temperature != null) 'temperature': temperature,
          if (speedRate != null) 'speed_rate': speedRate,
          if (instruct != null) 'instruct': instruct,
        },
      );
      return response.statusCode == 200 ? 'success' : 'failed';
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<List<ReferenceAudio>> getReferenceAudios() async {
    try {
      final response = await _client.get('/tts/reference/list');
      if (response.statusCode == 200) {
        final data = response.data;
        if (data is Map && data['data'] != null) {
          return (data['data'] as List)
              .map((json) => ReferenceAudio.fromJson(json))
              .toList();
        } else if (data is List) {
          return data.map((json) => ReferenceAudio.fromJson(json)).toList();
        }
      }
      return [];
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<ReferenceAudio> getReferenceAudioDetail(int id) async {
    try {
      final response = await _client.get('/tts/reference/$id');
      if (response.statusCode == 200) {
        final data = response.data;
        if (data is Map && data['data'] != null) {
          return ReferenceAudio.fromJson(data['data']);
        }
      }
      throw ApiException('Reference audio not found',
          statusCode: response.statusCode);
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  String getReferenceAudioUrl(int id) {
    return '${DioClient.baseUrl}/tts/reference/$id/audio';
  }

  Future<ReferenceAudio> uploadReferenceAudio({
    required String filePath,
    required String name,
    String? refText,
    String? language,
    double exaggeration = 0.5,
    double temperature = 0.8,
    String? instruct,
    double speedRate = 1.0,
    bool isDefault = false,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(filePath),
        'name': name,
        'ref_text': refText ?? '',
        if (language != null && language.isNotEmpty) 'language': language,
        'exaggeration': exaggeration,
        'temperature': temperature,
        if (instruct != null && instruct.isNotEmpty) 'instruct': instruct,
        'speed_rate': speedRate,
        'is_default': isDefault,
      });

      final response = await _client.postMultipart('/tts/reference/upload',
          formData: formData);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return ReferenceAudio.fromJson(response.data['data']);
      }
      throw ApiException('Upload failed', statusCode: response.statusCode);
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<void> deleteReferenceAudio(dynamic id) async {
    try {
      final idValue = id is String ? int.tryParse(id) ?? id : id;
      await _client.delete('/tts/reference/$idValue');
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<ReferenceAudio> updateReferenceAudio({
    required int id,
    String? name,
    String? refText,
    String? language,
    double? exaggeration,
    double? temperature,
    String? instruct,
    double? speedRate,
    bool? isDefault,
  }) async {
    try {
      final formData = FormData.fromMap({
        if (name != null && name.isNotEmpty) 'name': name,
        'ref_text': refText ?? '',
        if (language != null) 'language': language,
        if (exaggeration != null) 'exaggeration': exaggeration,
        if (temperature != null) 'temperature': temperature,
        if (instruct != null) 'instruct': instruct,
        if (speedRate != null) 'speed_rate': speedRate,
        if (isDefault != null) 'is_default': isDefault,
      });

      final response = await _client.post('/tts/reference/$id', data: formData);

      if (response.statusCode == 200) {
        final data = response.data;
        if (data is Map && data['data'] != null) {
          return ReferenceAudio.fromJson(data['data']);
        }
      }
      throw ApiException('Update failed', statusCode: response.statusCode);
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<ReferenceAudio> setDefaultReference(int referenceId) async {
    try {
      final response =
          await _client.post('/tts/reference/default/$referenceId');
      if (response.statusCode == 200) {
        final data = response.data;
        if (data is Map && data['data'] != null) {
          return ReferenceAudio.fromJson(data['data']);
        }
      }
      throw ApiException('Failed to set default',
          statusCode: response.statusCode);
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }

  Future<String> cloneVoice({
    required String text,
    required String filePath,
    String? language,
    String? refText,
    double exaggeration = 0.5,
    double temperature = 0.8,
    String? instruct,
    double speedRate = 1.0,
  }) async {
    try {
      final formData = FormData.fromMap({
        'text': text,
        'audio_prompt': await MultipartFile.fromFile(filePath),
        if (language != null && language.isNotEmpty) 'language': language,
        if (refText != null && refText.isNotEmpty) 'ref_text': refText,
        'exaggeration': exaggeration,
        'temperature': temperature,
        if (instruct != null && instruct.isNotEmpty) 'instruct': instruct,
        'speed_rate': speedRate,
      });

      final response =
          await _client.postMultipart('/tts/clone', formData: formData);
      return response.statusCode == 200 ? 'success' : 'failed';
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Network error',
          statusCode: e.response?.statusCode);
    }
  }
}
