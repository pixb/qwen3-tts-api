# Qwen3 TTS Frontend

A professional Flutter frontend application for Text-to-Speech (TTS) audio generation management.

## Features

- **Audio Generation**: Convert text to natural speech with high-quality voice synthesis
- **Reference Audio Management**: Upload, list, and delete reference audio files
- **Long Text Clone**: Split long text into chunks and generate audio for each chunk
- **Professional UI**: Modern, clean design with Material Design 3
- **Audio Playback**: Built-in audio player for previewing generated and reference audios

## Getting Started

### Prerequisites

- Flutter SDK 3.0+
- Dart SDK 3.0+

### Installation

1. Clone the repository
2. Navigate to the flutter_frontend directory
3. Install dependencies:

```bash
flutter pub get
```

4. Run the app:

```bash
flutter run
```

## Configuration

### API Configuration

The app is configured to connect to a backend API. Update the `baseUrl` in the following files to point to your API server:

- `lib/services/api_service.dart`
- `lib/screens/audio_generation_screen.dart`
- `lib/screens/reference_management_screen.dart`

Default URL: `http://localhost:8080`

### API Endpoints

The app expects the following endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tts/generate` | Generate audio from text |
| GET | `/api/tts/audio/{id}` | Get generated audio |
| GET | `/api/reference-audio` | List reference audios |
| POST | `/api/reference-audio` | Upload reference audio |
| DELETE | `/api/reference-audio/{id}` | Delete reference audio |
| POST | `/text/split` | Split long text into chunks |

## Long Text Clone

The "Long Text Clone" tab provides a workflow for generating audio from long texts by splitting them into manageable chunks.

### Workflow

1. **Input Text**: Enter or paste long text in the text input area
2. **Configure Split**: Adjust the max chunk length using the slider (50-500 characters)
3. **Split Text**: Click "Split" button to call `/text/split` API
4. **Review Chunks**: View the split results as a numbered list with character counts
5. **Select Chunk**: Click on any chunk to copy it to the input field
6. **Generate Audio**: Click "Generate" to create audio for the selected chunk
7. **Repeat**: Select next chunk and generate audio for each one

### UI Components

- **Text Splitting Controls**: Slider for max length + Split button
- **Split Chunks List**: Numbered list showing all chunks with:
  - Sequence number
  - Text preview (up to 3 lines)
  - Character count
  - Copy button (click to load chunk into input field)

### API Request

```
POST /text/split
Content-Type: application/json

{
  "text": "your long text here...",
  "max_length": 200
}
```

### API Response

```json
{
  "success": true,
  "chunks": ["chunk1", "chunk2", "..."],
  "chunk_count": 5,
  "original_length": 850,
  "max_length": 200
}
```

## Project Structure

```
lib/
├── main.dart                    # App entry point
├── models/
│   └── audio_models.dart        # Data models
├── screens/
│   ├── home_screen.dart         # Dashboard/Home screen
│   ├── audio_generation_screen.dart  # Audio generation
│   └── reference_management_screen.dart  # Reference audio management
├── services/
│   └── api_service.dart         # API service layer
├── theme/
│   └── app_theme.dart           # App theming
└── widgets/
    ├── common_widgets.dart      # Reusable widgets
    └── audio_player_widget.dart # Audio player component
```

## Dependencies

- `http`: HTTP client for API calls
- `just_audio`: Audio playback
- `file_picker`: File selection for uploads
- `path_provider`: File system access
- `intl`: Internationalization

## License

MIT License
