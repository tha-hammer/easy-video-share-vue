# Metronic UI Development Rules

## Project Overview

This is a video sharing application being migrated from vanilla JavaScript to Vue.js 3 + TypeScript with Metronic UI template. The backend uses AWS (S3, DynamoDB, Lambda, API Gateway, Cognito) and should remain unchanged.

## Technology Stack

- **Frontend**: Vue.js 3 + TypeScript + Vite
- **UI Framework**: Metronic Vue Template (demo8 layout)
- **Styling**: SCSS + Bootstrap 5 + Metronic components
- **State Management**: Pinia
- **Authentication**: AWS Cognito (existing system - do not change)
- **Backend**: AWS Lambda + API Gateway + DynamoDB (existing - do not change)
- **File Storage**: AWS S3 with multipart upload support

## Architecture Patterns

### 1. Component Structure (Follow Metronic Patterns)

```
src/
├── layouts/
│   ├── DefaultLayout.vue          # Main app layout with sidebar/header
│   ├── AuthLayout.vue             # Authentication pages layout
│   └── components/
│       ├── header/                # Header components
│       ├── aside/                 # Sidebar components
│       └── footer/                # Footer components
├── views/
│   ├── Dashboard.vue              # Main dashboard with video widgets
│   ├── Videos.vue                 # Video management page
│   ├── Upload.vue                 # Video upload page
│   └── admin/                     # Admin-specific views
├── components/
│   ├── widgets/                   # Video-specific widgets
│   │   ├── VideoUploadWidget.vue
│   │   ├── VideoStatsWidget.vue
│   │   ├── RecentVideosWidget.vue
│   │   └── VideoProgressWidget.vue
│   ├── video/                     # Video-specific components
│   │   ├── VideoPlayer.vue
│   │   ├── VideoCard.vue
│   │   ├── VideoList.vue
│   │   └── VideoModal.vue
│   └── forms/                     # Form components
│       ├── VideoUploadForm.vue
│       └── VideoMetadataForm.vue
└── stores/                        # Pinia stores
    ├── auth.ts                    # Authentication state
    ├── videos.ts                  # Video data management
    ├── upload.ts                  # Upload progress/state
    └── admin.ts                   # Admin functionality
```

### 2. Metronic Integration Rules

#### Layout Components

- Use Metronic's DefaultLayout as base template
- Implement KTAside (sidebar) with video-specific menu items
- Use KTHeader with user authentication status
- Follow Metronic's responsive design patterns

#### Widget Patterns

- Follow `metronic_vue_v8.3.0_demo8/src/components/widgets/` patterns
- Create video-specific widgets using Metronic's widget base classes
- Use consistent card layouts: `card`, `card-header`, `card-body`
- Implement hover effects: `hoverable`, `card-xl-stretch`

#### Component Naming

- Prefix video components with `Video` (VideoCard, VideoPlayer)
- Prefix widgets with `Widget` (VideoStatsWidget)
- Use PascalCase for component names
- Follow Metronic's component structure and props pattern

### 3. Data Models (Based on Terraform Schema)

#### Video Metadata

```typescript
interface VideoMetadata {
  video_id: string // Primary key: userId_timestamp_random
  user_id: string // Cognito user sub (UUID)
  user_email: string // Display email
  title: string // Video title
  filename: string // Original filename
  bucket_location: string // S3 object key
  upload_date: string // ISO timestamp
  file_size?: number // File size in bytes
  content_type?: string // MIME type
  duration?: number // Video duration in seconds
  created_at: string // ISO timestamp
  updated_at: string // ISO timestamp
}
```

#### User Data (From Cognito)

```typescript
interface User {
  userId: string // Cognito sub
  username: string // Cognito username
  email: string // User email
  groups: string[] // ['admin'] or ['user']
  isAdmin: boolean // Computed from groups
}
```

#### Upload Progress

```typescript
interface UploadProgress {
  videoId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'paused'
  estimatedTimeRemaining?: number
  uploadSpeed?: number
  chunkProgress: Map<number, number>
}
```

### 4. Authentication Rules

#### Keep Existing Auth System

- **DO NOT** use Metronic's auth store or components
- Keep existing AWS Cognito authentication flow
- Maintain current auth.js and auth-ui.js logic
- Integrate auth state with Pinia store for Vue components

#### Auth Integration Pattern

```typescript
// stores/auth.ts
import { defineStore } from 'pinia'
import { authManager } from '@/core/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    isAuthenticated: false,
    isLoading: true,
  }),

  actions: {
    async initialize() {
      // Integrate with existing authManager
      const isAuth = await authManager.initialize()
      this.isAuthenticated = isAuth
      if (isAuth) {
        this.user = authManager.getCurrentUser()
      }
      this.isLoading = false
    },
  },
})
```

### 5. Video-Specific UI Patterns

#### Dashboard Widgets (Reference: Dashboard.vue)

- **VideoStatsWidget**: Total videos, storage used, upload count
- **RecentVideosWidget**: Latest uploaded videos
- **UploadProgressWidget**: Active upload status
- **VideoAnalyticsWidget**: View counts, popular videos

#### Video Management

- **VideoCard Component**: Thumbnail, title, duration, actions
- **VideoList Component**: Grid/list view toggle
- **VideoPlayer Modal**: Full-screen video player
- **VideoUpload Component**: Drag-drop with progress

#### Admin Panel (Full Metronic Treatment)

- Use `kt-datatable` for user/video tables
- Implement modals for video management
- Use Metronic's statistics widgets for admin dashboard
- Follow Metronic's form patterns for admin actions

### 6. Upload System Rules

#### Multipart Upload Integration

- Keep existing S3 multipart upload logic
- Wrap in Vue composable: `useVideoUpload()`
- Provide reactive progress tracking
- Support pause/resume/cancel operations

#### Upload UI Components

```vue
<!-- VideoUploadWidget.vue -->
<template>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">Upload Video</h3>
    </div>
    <div class="card-body">
      <!-- Drag-drop area -->
      <!-- Progress indicators -->
      <!-- Upload controls -->
    </div>
  </div>
</template>
```

### 7. API Integration Rules

#### Keep Existing API Structure

- **DO NOT** change Lambda functions or API Gateway
- **DO NOT** modify DynamoDB schema
- Use existing endpoints:
  - `POST /videos` - Create video metadata
  - `GET /videos` - List user videos
  - `GET /admin/users` - Admin: list users
  - `GET /admin/videos` - Admin: list all videos
  - `DELETE /admin/videos` - Admin: delete video

#### API Service Pattern

```typescript
// services/VideoService.ts
export class VideoService {
  static async saveMetadata(metadata: VideoMetadata) {
    // Use existing API endpoints
  }

  static async getUserVideos(): Promise<VideoMetadata[]> {
    // Integration with existing API
  }
}
```

### 8. Styling Rules

#### SCSS Structure

```scss
// Follow Metronic's SCSS patterns
@import 'assets/sass/style';

// Video-specific styles
.video-card {
  @extend .card;
  // Custom video card styling
}

.upload-progress {
  // Upload progress styling
}
```

#### Component Styling

- Use Metronic's utility classes
- Follow Bootstrap 5 spacing/layout conventions
- Implement dark/light mode support (Metronic's theme system)
- Use Metronic's color palette and icon system

### 9. State Management Patterns

#### Pinia Stores

```typescript
// stores/videos.ts
export const useVideosStore = defineStore('videos', {
  state: () => ({
    videos: [] as VideoMetadata[],
    loading: false,
    uploadProgress: new Map<string, UploadProgress>(),
  }),

  actions: {
    async loadUserVideos() {
      // Load from API
    },

    updateUploadProgress(videoId: string, progress: UploadProgress) {
      // Update upload progress
    },
  },
})
```

### 10. Development Guidelines

#### Code Quality

- Use TypeScript strict mode
- Implement proper error handling
- Follow Vue 3 Composition API patterns
- Use Metronic's component props patterns

#### Testing Strategy

- Unit tests for composables
- Component tests for video widgets
- Integration tests for upload flow
- E2E tests for critical user journeys

#### Performance

- Lazy load video thumbnails
- Implement virtual scrolling for large video lists
- Optimize upload chunk sizes
- Use Vue's keep-alive for cached components

### 11. Migration Strategy

#### Phase 1: Core Infrastructure

1. Set up Vue 3 + TypeScript + Vite project
2. Install Metronic dependencies and configure
3. Create basic layout structure
4. Integrate existing auth system

#### Phase 2: Video Components

1. Create video-related components and widgets
2. Implement upload functionality with Vue wrappers
3. Build video listing and management UI
4. Test integration with existing APIs

#### Phase 3: Admin Panel

1. Build admin dashboard with Metronic widgets
2. Implement user management interface
3. Create video administration tools
4. Add admin-specific analytics

#### Phase 4: Polish & Optimization

1. Implement responsive design
2. Add advanced features (search, filters)
3. Performance optimization
4. Final testing and deployment

## Common Patterns to Follow

### Component Props (Metronic Style)

```typescript
// Widget components should accept these standard props
interface WidgetProps {
  widgetClasses?: string // Additional CSS classes
  title?: string // Widget title
  iconName?: string // Metronic icon name
  color?: string // Theme color variant
}
```

### Error Handling

```typescript
// Use Metronic's Notice component for user feedback
import Notice from '@/components/Notice.vue'

// Show success/error messages consistently
this.showStatus('success', 'Video uploaded successfully!')
this.showStatus('error', 'Upload failed. Please try again.')
```

### Responsive Design

- Follow Metronic's breakpoint patterns
- Use Bootstrap's grid system
- Implement mobile-first design
- Test on all device sizes

## Dependencies to Install

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.0.0",
    "pinia": "^2.1.0",
    "@aws-sdk/client-s3": "^3.832.0",
    "@aws-sdk/s3-request-presigner": "^3.832.0",
    "aws-amplify": "^6.0.7",
    "bootstrap": "^5.3.2",
    "bootstrap-icons": "^1.11.2",
    "apexcharts": "^3.40.0",
    "vue3-apexcharts": "^1.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.0.0",
    "sass": "^1.70.0",
    "vite": "^6.3.5"
  }
}
```

## File Naming Conventions

- Components: PascalCase (`VideoCard.vue`)
- Views: PascalCase (`Dashboard.vue`)
- Stores: camelCase (`videos.ts`, `auth.ts`)
- Services: PascalCase (`VideoService.ts`)
- Types: PascalCase (`VideoTypes.ts`)
- Composables: camelCase (`useVideoUpload.ts`)

## Remember

- **NEVER** modify backend infrastructure (Terraform, Lambda, DynamoDB)
- **ALWAYS** follow Metronic's component patterns and styling
- **MAINTAIN** existing authentication flow and API contracts
- **IMPLEMENT** responsive design and accessibility features
- **TEST** upload functionality thoroughly across different file sizes and network conditions
