import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:dio/dio.dart';
import '../models/audio_models.dart';
import 'api_provider.dart';

class ReferenceAudioState {
  final List<ReferenceAudio> audios;
  final bool isLoading;
  final bool isUploading;
  final String? error;
  final PlatformFile? selectedFile;
  final String? playingAudioId;
  final ReferenceAudio? defaultReference;
  final ReferenceAudio? selectedAudio;

  const ReferenceAudioState({
    this.audios = const [],
    this.isLoading = false,
    this.isUploading = false,
    this.error,
    this.selectedFile,
    this.playingAudioId,
    this.defaultReference,
    this.selectedAudio,
  });

  ReferenceAudioState copyWith({
    List<ReferenceAudio>? audios,
    bool? isLoading,
    bool? isUploading,
    String? error,
    PlatformFile? selectedFile,
    String? playingAudioId,
    ReferenceAudio? defaultReference,
    ReferenceAudio? selectedAudio,
    bool clearError = false,
    bool clearSelectedFile = false,
    bool clearPlayingAudio = false,
    bool clearSelectedAudio = false,
  }) {
    return ReferenceAudioState(
      audios: audios ?? this.audios,
      isLoading: isLoading ?? this.isLoading,
      isUploading: isUploading ?? this.isUploading,
      error: clearError ? null : (error ?? this.error),
      selectedFile:
          clearSelectedFile ? null : (selectedFile ?? this.selectedFile),
      playingAudioId:
          clearPlayingAudio ? null : (playingAudioId ?? this.playingAudioId),
      defaultReference: defaultReference ?? this.defaultReference,
      selectedAudio:
          clearSelectedAudio ? null : (selectedAudio ?? this.selectedAudio),
    );
  }
}

class ReferenceAudioNotifier extends StateNotifier<ReferenceAudioState> {
  final DioClient _dioClient;

  ReferenceAudioNotifier(this._dioClient) : super(const ReferenceAudioState());

  Future<void> refresh() async {
    await loadReferenceAudios();
  }

  Future<void> loadReferenceAudios() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _dioClient.get('/tts/reference/list');

      if (response.statusCode == 200) {
        final data = response.data;
        List<ReferenceAudio> audios = [];

        if (data is Map && data['data'] != null) {
          final List<dynamic> dataList = data['data'];
          audios =
              dataList.map((json) => ReferenceAudio.fromJson(json)).toList();
        } else if (data is List) {
          audios = data.map((json) => ReferenceAudio.fromJson(json)).toList();
        }

        // Find default reference
        ReferenceAudio? defaultRef;
        for (var audio in audios) {
          if (audio.isDefault) {
            defaultRef = audio;
            break;
          }
        }

        state = state.copyWith(
          audios: audios,
          isLoading: false,
          defaultReference: defaultRef,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Failed to load reference audios: ${response.statusCode}',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Network error: ${e.toString()}',
      );
    }
  }

  Future<ReferenceAudio?> getReferenceAudioDetail(int id) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _dioClient.get('/tts/reference/$id');

      if (response.statusCode == 200) {
        final data = response.data;
        ReferenceAudio? audio;

        if (data is Map && data['data'] != null) {
          audio = ReferenceAudio.fromJson(data['data']);
        }

        state = state.copyWith(
          selectedAudio: audio,
          isLoading: false,
        );
        return audio;
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Failed to load reference audio details',
        );
        return null;
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Network error: ${e.toString()}',
      );
      return null;
    }
  }

  String getReferenceAudioUrl(int id) {
    return '${DioClient.baseUrl}/tts/reference/$id/audio';
  }

  Future<void> loadDefaultReference() async {
    try {
      final response = await _dioClient.get('/tts/reference/default');

      if (response.statusCode == 200) {
        final data = response.data;
        if (data is Map && data['data'] != null) {
          final defaultRef = ReferenceAudio.fromJson(data['data']);
          state = state.copyWith(defaultReference: defaultRef);
        }
      }
    } catch (e) {
      // Ignore error for default reference
    }
  }

  Future<void> setDefaultReference(int referenceId) async {
    try {
      final response =
          await _dioClient.post('/tts/reference/default/$referenceId');

      if (response.statusCode == 200) {
        await loadReferenceAudios();
        _showSuccessMessage('Default reference audio set successfully');
      }
    } catch (e) {
      state = state.copyWith(error: 'Failed to set default: ${e.toString()}');
    }
  }

  void _showSuccessMessage(String message) {
    // This will be handled by the UI listening to state changes
  }

  Future<void> pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
        allowMultiple: false,
      );

      if (result != null && result.files.isNotEmpty) {
        state = state.copyWith(selectedFile: result.files.first);
      }
    } catch (e) {
      state = state.copyWith(error: 'Failed to pick file: ${e.toString()}');
    }
  }

  void clearSelectedFile() {
    state = state.copyWith(clearSelectedFile: true);
  }

  Future<void> uploadReferenceAudio({
    required String name,
    String? refText,
    String? language,
    double exaggeration = 0.5,
    double temperature = 0.8,
    String? instruct,
    double speedRate = 1.0,
    bool isDefault = false,
  }) async {
    if (state.selectedFile == null) {
      state = state.copyWith(error: 'Please select a file first');
      return;
    }

    state = state.copyWith(isUploading: true, clearError: true);

    try {
      late MultipartFile file;
      bool hasPath = false;

      // Try to check if path is available (for mobile platforms)
      try {
        hasPath = state.selectedFile!.path != null;
      } catch (_) {
        // On web, accessing path will throw an exception
        hasPath = false;
      }

      if (hasPath) {
        // For mobile platforms
        file = await MultipartFile.fromFile(
          state.selectedFile!.path!,
          filename: state.selectedFile!.name,
        );
      } else if (state.selectedFile!.bytes != null) {
        // For web platform
        file = MultipartFile.fromBytes(
          state.selectedFile!.bytes!,
          filename: state.selectedFile!.name,
        );
      } else {
        state = state.copyWith(
          isUploading: false,
          error: 'No file data available',
        );
        return;
      }

      final formData = FormData.fromMap({
        'file': file,
        'name': name,
        'ref_text': refText ?? '',
        if (language != null && language.isNotEmpty) 'language': language,
        'exaggeration': exaggeration,
        'temperature': temperature,
        if (instruct != null && instruct.isNotEmpty) 'instruct': instruct,
        'speed_rate': speedRate,
        'is_default': isDefault,
      });

      final response = await _dioClient.postMultipart('/tts/reference/upload',
          formData: formData);

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = response.data;
        ReferenceAudio? newAudio;

        if (data is Map && data['data'] != null) {
          newAudio = ReferenceAudio.fromJson(data['data']);
        }

        if (newAudio != null) {
          // Update is_default for other audios if this one is set as default
          List<ReferenceAudio> updatedAudios;
          if (newAudio.isDefault) {
            updatedAudios = state.audios.map((a) {
              return a.copyWith(isDefault: false);
            }).toList();
            updatedAudios.insert(0, newAudio);
          } else {
            updatedAudios = [newAudio, ...state.audios];
          }

          state = state.copyWith(
            audios: updatedAudios,
            isUploading: false,
            clearSelectedFile: true,
            defaultReference:
                newAudio.isDefault ? newAudio : state.defaultReference,
          );
        } else {
          state = state.copyWith(isUploading: false, clearSelectedFile: true);
          await loadReferenceAudios();
        }
      } else {
        state = state.copyWith(
          isUploading: false,
          error: 'Failed to upload',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isUploading: false,
        error: 'Upload failed: ${e.toString()}',
      );
    }
  }

  Future<void> deleteReferenceAudio(dynamic id) async {
    state = state.copyWith(isLoading: true, clearError: true);

    final idValue = id is String ? int.tryParse(id) ?? id : id;
    final path = '/tts/reference/$idValue';

    try {
      final response = await _dioClient.delete(path);

      if (response.statusCode == 200 || response.statusCode == 204) {
        final deletedAudio = state.audios.firstWhere(
          (audio) => audio.id == id.toString(),
          orElse: () => ReferenceAudio(id: '', name: ''),
        );

        state = state.copyWith(
          audios:
              state.audios.where((audio) => audio.id != id.toString()).toList(),
          isLoading: false,
          clearPlayingAudio: true,
          defaultReference:
              deletedAudio.isDefault ? null : state.defaultReference,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Failed to delete reference audio',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Delete failed: ${e.toString()}',
      );
    }
  }

  Future<void> updateReferenceAudio({
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
    state = state.copyWith(isLoading: true, clearError: true);

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

      final response =
          await _dioClient.post('/tts/reference/$id', data: formData);

      if (response.statusCode == 200) {
        final data = response.data;
        ReferenceAudio? updatedAudio;

        if (data is Map && data['data'] != null) {
          updatedAudio = ReferenceAudio.fromJson(data['data']);
        }

        if (updatedAudio != null) {
          final ReferenceAudio newAudio = updatedAudio;
          // Update the audio in the list
          final List<ReferenceAudio> updatedAudios = state.audios.map((audio) {
            if (audio.id == id.toString()) {
              return newAudio;
            }
            // If setting this as default, unset others
            if (newAudio.isDefault && audio.isDefault) {
              return audio.copyWith(isDefault: false);
            }
            return audio;
          }).toList();

          state = state.copyWith(
            audios: updatedAudios,
            isLoading: false,
            defaultReference:
                newAudio.isDefault ? newAudio : state.defaultReference,
          );
        } else {
          state = state.copyWith(isLoading: false);
          await loadReferenceAudios();
        }
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Failed to update reference audio',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Update failed: ${e.toString()}',
      );
    }
  }

  void setPlayingAudio(String? audioId) {
    if (state.playingAudioId == audioId) {
      state = state.copyWith(clearPlayingAudio: true);
    } else {
      state = state.copyWith(playingAudioId: audioId);
    }
  }

  void setSelectedAudio(ReferenceAudio? audio) {
    if (audio == null) {
      state = state.copyWith(clearSelectedAudio: true);
    } else {
      state = state.copyWith(selectedAudio: audio);
    }
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

final referenceAudioProvider =
    StateNotifierProvider<ReferenceAudioNotifier, ReferenceAudioState>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return ReferenceAudioNotifier(dioClient);
});
