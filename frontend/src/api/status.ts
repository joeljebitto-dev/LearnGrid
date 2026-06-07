export async function getFrontendStatus() {
  return {
    serviceId: import.meta.env.VITE_SERVICE_ID ?? 'SVC-011',
    serviceName: import.meta.env.VITE_SERVICE_NAME ?? 'frontend-service',
    status: 'ok'
  };
}

