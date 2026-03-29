import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import '../theme/app_theme.dart';

class MyCustomSource extends StreamAudioSource {
  final Uint8List _bytes;

  MyCustomSource(this._bytes);

  @override
  Future<StreamAudioResponse> request([int? start, int? end]) async {
    start ??= 0;
    end ??= _bytes.length;
    return StreamAudioResponse(
      sourceLength: _bytes.length,
      contentLength: end - start,
      offset: start,
      stream: Stream.value(_bytes.sublist(start, end)),
      contentType: 'audio/wav',
    );
  }
}

class AudioPlayerWidget extends StatefulWidget {
  final String? audioUrl;
  final Uint8List? audioBytes;
  final String? localPath;
  final bool autoPlay;
  final VoidCallback? onComplete;

  const AudioPlayerWidget({
    super.key,
    this.audioUrl,
    this.audioBytes,
    this.localPath,
    this.autoPlay = false,
    this.onComplete,
  });

  @override
  State<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends State<AudioPlayerWidget> {
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isLoading = true;
  bool _isPlaying = false;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;
  String? _error;

  @override
  void initState() {
    super.initState();
    _initAudio();
  }

  Future<void> _initAudio() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      String? source;
      if (widget.audioBytes != null && widget.audioBytes!.isNotEmpty) {
        await _audioPlayer.setAudioSource(
          MyCustomSource(widget.audioBytes!),
          preload: true,
        );
        source = 'bytes';
      } else if (widget.localPath != null && widget.localPath!.isNotEmpty) {
        source = widget.localPath!;
        await _audioPlayer.setFilePath(source);
      } else if (widget.audioUrl != null && widget.audioUrl!.isNotEmpty) {
        source = widget.audioUrl!;
        await _audioPlayer.setUrl(source);
      }

      if (source != null) {
        _duration = _audioPlayer.duration ?? Duration.zero;

        _audioPlayer.positionStream.listen((position) {
          if (mounted) {
            setState(() {
              _position = position;
            });
          }
        });

        _audioPlayer.playerStateStream.listen((state) {
          if (mounted) {
            setState(() {
              _isPlaying = state.playing;
            });
            if (state.processingState == ProcessingState.completed) {
              widget.onComplete?.call();
              _audioPlayer.seek(Duration.zero);
              _audioPlayer.pause();
            }
          }
        });

        if (widget.autoPlay) {
          await _audioPlayer.play();
        }
      }

      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = 'Failed to load audio: ${e.toString()}';
      });
    }
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    if (widget.audioUrl == null && widget.localPath == null) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.primaryColor.withOpacity(0.2),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              _buildPlayButton(),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildProgressBar(),
                    const SizedBox(height: 8),
                    _buildTimeLabels(),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPlayButton() {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.primaryColor, AppTheme.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryColor.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _isLoading || _error != null
              ? null
              : () {
                  if (_isPlaying) {
                    _audioPlayer.pause();
                  } else {
                    _audioPlayer.play();
                  }
                },
          borderRadius: BorderRadius.circular(28),
          child: Center(
            child: _isLoading
                ? const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : Icon(
                    _isPlaying ? Icons.pause : Icons.play_arrow,
                    color: Colors.white,
                    size: 32,
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildProgressBar() {
    final progress = _duration.inMilliseconds > 0
        ? _position.inMilliseconds / _duration.inMilliseconds
        : 0.0;

    return SliderTheme(
      data: SliderTheme.of(context).copyWith(
        trackHeight: 4,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
        overlayShape: const RoundSliderOverlayShape(overlayRadius: 14),
        activeTrackColor: AppTheme.primaryColor,
        inactiveTrackColor: AppTheme.primaryColor.withOpacity(0.2),
        thumbColor: AppTheme.primaryColor,
        overlayColor: AppTheme.primaryColor.withOpacity(0.2),
      ),
      child: Slider(
        value: progress.clamp(0.0, 1.0),
        onChanged: (value) {
          final position = Duration(
            milliseconds: (value * _duration.inMilliseconds).round(),
          );
          _audioPlayer.seek(position);
        },
      ),
    );
  }

  Widget _buildTimeLabels() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          _formatDuration(_position),
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
            fontWeight: FontWeight.w500,
          ),
        ),
        Text(
          _formatDuration(_duration),
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
