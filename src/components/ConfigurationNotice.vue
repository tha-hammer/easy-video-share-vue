<template>
  <div class="notice d-flex bg-light-warning rounded border-warning border border-dashed p-6">
    <i class="ki-duotone ki-information-5 fs-2tx text-warning me-4">
      <span class="path1"></span>
      <span class="path2"></span>
      <span class="path3"></span>
    </i>
    <div class="d-flex flex-stack flex-grow-1">
      <div class="fw-semibold">
        <h4 class="text-gray-900 fw-bold">API Configuration Required</h4>
        <div class="fs-6 text-gray-700">
          <p>To connect to your AWS backend, you need to configure environment variables:</p>

          <div class="my-4">
            <h6>1. Create a <code>.env.local</code> file in your project root:</h6>
            <div class="bg-light-dark p-4 rounded mt-2">
              <code class="text-gray-800">
                # AWS Configuration<br />
                VITE_AWS_REGION=us-east-1<br />
                VITE_AWS_BUCKET_NAME=your-bucket-name<br />
                VITE_AWS_ACCESS_KEY_ID=your-access-key<br />
                VITE_AWS_SECRET_ACCESS_KEY=your-secret-key<br />
                <br />
                # Cognito Configuration<br />
                VITE_COGNITO_REGION=us-east-1<br />
                VITE_COGNITO_USER_POOL_ID=your-user-pool-id<br />
                VITE_COGNITO_CLIENT_ID=your-client-id<br />
                <br />
                # API Configuration<br />
                VITE_API_ENDPOINT=https://your-api-gateway-url/dev<br />
                VITE_API_VIDEOS_ENDPOINT=https://your-api-gateway-url/dev/videos
              </code>
            </div>
          </div>

          <div class="my-4">
            <h6>2. Configure CORS in your AWS API Gateway:</h6>
            <ul class="mb-0">
              <li>Add <code>http://localhost:5173</code> to allowed origins</li>
              <li>Include headers: <code>Content-Type, Authorization</code></li>
              <li>Allow methods: <code>GET, POST, DELETE, OPTIONS</code></li>
            </ul>
          </div>

          <div class="my-4">
            <h6>3. Restart the development server:</h6>
            <div class="bg-light-dark p-2 rounded mt-2">
              <code class="text-gray-800">npm run dev</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ConfigurationNotice',
})
</script>
