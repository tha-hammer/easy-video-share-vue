<template>
  <div class="text-overlay-demo-simple">
    <!-- Header -->
    <div class="demo-header mb-6">
      <h1 class="display-6 fw-bold text-gray-900 mb-2">Text Overlay System Demo</h1>
      <p class="text-muted fs-5">
        Interactive text overlay editing for video segments - Phase 1 Implementation
      </p>
    </div>

    <!-- Feature Overview -->
    <div class="features-grid row g-4 mb-8">
      <div class="col-md-4">
        <div class="feature-card card h-100">
          <div class="card-body text-center">
            <KTIcon icon-name="design" icon-class="fs-3x text-primary mb-3" />
            <h5 class="card-title">Fabric.js Canvas</h5>
            <p class="card-text text-muted">
              Interactive canvas for placing and editing text overlays with real-time preview
            </p>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="feature-card card h-100">
          <div class="card-body text-center">
            <KTIcon icon-name="code" icon-class="fs-3x text-success mb-3" />
            <h5 class="card-title">FFmpeg Integration</h5>
            <p class="card-text text-muted">
              Automatic coordinate translation to FFmpeg drawtext filters for video processing
            </p>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="feature-card card h-100">
          <div class="card-body text-center">
            <KTIcon icon-name="setting-2" icon-class="fs-3x text-warning mb-3" />
            <h5 class="card-title">Advanced Controls</h5>
            <p class="card-text text-muted">
              Font styling, colors, effects, positioning, and timeline controls
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Implementation Status -->
    <div class="implementation-status card mb-6">
      <div class="card-header">
        <h3 class="card-title">Implementation Progress</h3>
      </div>
      <div class="card-body">
        <div class="row g-4">
          <div class="col-md-6">
            <h6 class="fw-bold text-success mb-3">✅ Completed (Phase 1)</h6>
            <ul class="list-unstyled">
              <li class="mb-2">
                <KTIcon icon-name="check" icon-class="text-success me-2" />
                Fabric.js installation and TypeScript types
              </li>
              <li class="mb-2">
                <KTIcon icon-name="check" icon-class="text-success me-2" />
                Core text overlay data models
              </li>
              <li class="mb-2">
                <KTIcon icon-name="check" icon-class="text-success me-2" />
                TextOverlayService composable with coordinate translation
              </li>
              <li class="mb-2">
                <KTIcon icon-name="check" icon-class="text-success me-2" />
                SegmentTextEditor Vue component
              </li>
              <li class="mb-2">
                <KTIcon icon-name="check" icon-class="text-success me-2" />
                Pinia store for state management
              </li>
            </ul>
          </div>

          <div class="col-md-6">
            <h6 class="fw-bold text-primary mb-3">🔄 Ready for Integration</h6>
            <ul class="list-unstyled">
              <li class="mb-2">
                <KTIcon icon-name="loading" icon-class="text-primary me-2" />
                Canvas initialization and background images
              </li>
              <li class="mb-2">
                <KTIcon icon-name="loading" icon-class="text-primary me-2" />
                Text object creation and manipulation
              </li>
              <li class="mb-2">
                <KTIcon icon-name="loading" icon-class="text-primary me-2" />
                Font and styling controls
              </li>
              <li class="mb-2">
                <KTIcon icon-name="loading" icon-class="text-primary me-2" />
                Undo/redo functionality
              </li>
              <li class="mb-2">
                <KTIcon icon-name="loading" icon-class="text-primary me-2" />
                FFmpeg filter generation
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Code Architecture -->
    <div class="architecture-overview card mb-6">
      <div class="card-header">
        <h3 class="card-title">System Architecture</h3>
      </div>
      <div class="card-body">
        <div class="architecture-diagram">
          <div class="row text-center">
            <div class="col-md-3">
              <div class="arch-box">
                <KTIcon icon-name="design-frame" icon-class="fs-2x text-primary mb-2" />
                <h6>SegmentTextEditor.vue</h6>
                <small class="text-muted">Main UI Component</small>
              </div>
            </div>
            <div class="col-md-3">
              <div class="arch-box">
                <KTIcon icon-name="code" icon-class="fs-2x text-info mb-2" />
                <h6>useTextOverlay.ts</h6>
                <small class="text-muted">Core Composable</small>
              </div>
            </div>
            <div class="col-md-3">
              <div class="arch-box">
                <KTIcon icon-name="data" icon-class="fs-2x text-success mb-2" />
                <h6>textOverlays.ts</h6>
                <small class="text-muted">Pinia Store</small>
              </div>
            </div>
            <div class="col-md-3">
              <div class="arch-box">
                <KTIcon icon-name="setting" icon-class="fs-2x text-warning mb-2" />
                <h6>textOverlay.ts</h6>
                <small class="text-muted">Type Definitions</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Code Examples -->
    <div class="code-examples card mb-6">
      <div class="card-header">
        <h3 class="card-title">Usage Examples</h3>
      </div>
      <div class="card-body">
        <div class="row g-4">
          <div class="col-lg-6">
            <h6 class="fw-bold mb-3">1. Component Usage</h6>
            <div class="code-block">
              <pre><code>&lt;SegmentTextEditor
  :segment-id="'segment_123'"
  :thumbnail-url="thumbnailUrl"
  :video-width="1920"
  :video-height="1080"
  :segment-duration="30"
  @text-overlays-changed="handleOverlaysChanged"
  @ffmpeg-filters-generated="handleFiltersGenerated"
/&gt;</code></pre>
            </div>
          </div>

          <div class="col-lg-6">
            <h6 class="fw-bold mb-3">2. Store Integration</h6>
            <div class="code-block">
              <pre><code>import { useTextOverlayStore } from '@/stores/textOverlays'

const store = useTextOverlayStore()

// Get overlays for a segment
const overlays = store.getOverlaysForSegment('segment_123')

// Add new overlay
store.addOverlay(segmentId, newOverlay)

// Generate FFmpeg filters
const filters = store.generateFFmpegFilters(segmentId)</code></pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Next Steps -->
    <div class="next-steps card">
      <div class="card-header">
        <h3 class="card-title">Next Steps for Development</h3>
      </div>
      <div class="card-body">
        <div class="row g-4">
          <div class="col-md-6">
            <h6 class="fw-bold text-primary mb-3">Phase 2: Canvas Integration</h6>
            <ol class="list-numbered">
              <li>Install Fabric.js package dependencies</li>
              <li>Initialize canvas with video thumbnail background</li>
              <li>Implement text object creation and selection</li>
              <li>Add drag-and-drop positioning</li>
              <li>Enable inline text editing</li>
            </ol>
          </div>

          <div class="col-md-6">
            <h6 class="fw-bold text-success mb-3">Phase 3: Advanced Features</h6>
            <ol class="list-numbered">
              <li>Font family and styling controls</li>
              <li>Color pickers and transparency</li>
              <li>Text effects (shadows, outlines)</li>
              <li>Timeline and duration controls</li>
              <li>Template system for reusable styles</li>
            </ol>
          </div>
        </div>

        <div class="alert alert-info mt-4">
          <KTIcon icon-name="information-5" icon-class="fs-2x text-info me-3" />
          <div>
            <strong>Ready for Development:</strong> All core infrastructure is in place. The next
            step is to run <code>npm install fabric @types/fabric</code> and begin implementing the
            canvas initialization in the useTextOverlay composable.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'TextOverlayDemoSimple',
  setup() {
    return {}
  },
})
</script>

<style scoped>
.text-overlay-demo-simple {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.demo-header {
  text-align: center;
  margin-bottom: 2rem;
}

.feature-card {
  transition: transform 0.2s ease-in-out;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.arch-box {
  padding: 20px;
  border: 2px dashed #e1e5e9;
  border-radius: 8px;
  margin-bottom: 15px;
  transition: border-color 0.2s ease-in-out;
}

.arch-box:hover {
  border-color: #3699ff;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
}

.list-numbered {
  padding-left: 0;
  counter-reset: step-counter;
}

.list-numbered li {
  counter-increment: step-counter;
  margin-bottom: 8px;
  padding-left: 30px;
  position: relative;
}

.list-numbered li::before {
  content: counter(step-counter);
  position: absolute;
  left: 0;
  top: 0;
  background: #3699ff;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
}

.architecture-diagram {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

/* Responsive */
@media (max-width: 768px) {
  .text-overlay-demo-simple {
    padding: 16px;
  }

  .arch-box {
    margin-bottom: 20px;
  }
}
</style>
