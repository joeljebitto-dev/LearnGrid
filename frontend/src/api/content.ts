import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type ContentAsset = Entity & {
  institution_id?: string;
  owner_profile_id?: string;
  asset_type?: string;
  metadata?: Record<string, unknown>;
  file_metadata?: Record<string, unknown> | null;
};

export type PresignedUploadPayload = {
  institution_id: string;
  owner_profile_id: string;
  asset_type: string;
  title: string;
  metadata?: Record<string, unknown>;
  file_name: string;
  mime_type: string;
  file_size_bytes: number;
  checksum_sha256?: string | null;
};

export type PresignedUploadResponse = {
  asset: ContentAsset;
  object_key: string;
  upload_url: string;
  upload_headers: Record<string, string>;
  expires_at: string;
};

export async function listContentAssets(params?: QueryParams): Promise<ListResponse<ContentAsset>> {
  const response = await apiClient.get<ListResponse<ContentAsset>>('/content/assets/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createPresignedUpload(
  payload: PresignedUploadPayload
): Promise<PresignedUploadResponse> {
  const response = await apiClient.post<PresignedUploadResponse>(
    '/content/assets/uploads/presigned/',
    payload
  );
  return response.data;
}

export async function completePresignedUpload(
  assetId: string,
  payload: { checksum_sha256?: string | null }
): Promise<ContentAsset> {
  const response = await apiClient.post<ContentAsset>(
    `/content/assets/${assetId}/uploads/complete/`,
    payload
  );
  return response.data;
}

export async function proxyUploadAsset(payload: {
  institution_id: string;
  owner_profile_id: string;
  asset_type: string;
  title: string;
  file: File;
  metadata?: Record<string, unknown>;
}): Promise<ContentAsset> {
  const formData = new FormData();
  formData.append('institution_id', payload.institution_id);
  formData.append('owner_profile_id', payload.owner_profile_id);
  formData.append('asset_type', payload.asset_type);
  formData.append('title', payload.title);
  formData.append('file', payload.file);
  if (payload.metadata) {
    formData.append('metadata', JSON.stringify(payload.metadata));
  }
  const response = await apiClient.post<ContentAsset>('/content/assets/uploads/proxy/', formData);
  return response.data;
}

export async function createSignedAccess(
  assetId: string,
  requestedByProfileId: string
): Promise<Record<string, unknown>> {
  const response = await apiClient.post<Record<string, unknown>>(`/content/assets/${assetId}/access/`, {
    requested_by_profile_id: requestedByProfileId
  });
  return response.data;
}
