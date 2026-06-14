import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import type { SessionContext } from '../../api/auth';
import {
  completePresignedUpload,
  createPresignedUpload,
  listContentAssets,
  proxyUploadAsset
} from '../../api/content';
import { PortalLayout } from '../layout/PortalLayout';
import {
  buttonClass,
  EntityList,
  ErrorState,
  fieldClass,
  Field,
  JsonPreview,
  LoadingState,
  PageHeader,
  Panel
} from '../shared/ui';

export function ContentUploadPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const assetsQuery = useQuery({
    queryKey: ['content-assets', context.profile.institution_id],
    queryFn: () =>
      listContentAssets({
        institution_id: context.profile.institution_id ?? undefined,
        owner_profile_id: context.profile.id,
        page_size: 20,
        sort: '-updated_at'
      })
  });
  const presignedMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createPresignedUpload({
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        owner_profile_id: context.profile.id,
        asset_type: String(data.get('asset_type') || 'document'),
        title: String(data.get('title') || ''),
        file_name: String(data.get('file_name') || ''),
        mime_type: String(data.get('mime_type') || 'application/octet-stream'),
        file_size_bytes: Number(data.get('file_size_bytes') || 1),
        checksum_sha256: String(data.get('checksum_sha256') || '') || null,
        metadata: {}
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['content-assets'] });
    }
  });
  const completeMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return completePresignedUpload(String(data.get('asset_id') || ''), {
        checksum_sha256: String(data.get('checksum_sha256') || '') || null
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['content-assets'] });
    }
  });
  const proxyMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      if (!selectedFile) {
        throw new Error('Select a file before uploading.');
      }
      const data = new FormData(form);
      return proxyUploadAsset({
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        owner_profile_id: context.profile.id,
        asset_type: String(data.get('asset_type') || 'document'),
        title: String(data.get('title') || selectedFile.name),
        file: selectedFile,
        metadata: {}
      });
    },
    onSuccess: async () => {
      setSelectedFile(null);
      await queryClient.invalidateQueries({ queryKey: ['content-assets'] });
    }
  });

  return (
    <PortalLayout context={context} activeNav="content-upload">
      <PageHeader
        title="Content Upload"
        description="Create presigned uploads, complete MinIO uploads, and upload proxy files through content-service."
      />
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel title="Presigned upload">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              presignedMutation.mutate(event.currentTarget);
            }}
          >
            <Field htmlFor="pre-title" label="Title">
              <input id="pre-title" name="title" className={fieldClass} required />
            </Field>
            <Field htmlFor="pre-institution" label="Institution ID">
              <input id="pre-institution" name="institution_id" className={fieldClass} defaultValue={context.profile.institution_id ?? ''} required />
            </Field>
            <Field htmlFor="pre-type" label="Asset type">
              <select id="pre-type" name="asset_type" className={fieldClass}>
                <option value="document">Document</option>
                <option value="video">Video</option>
                <option value="image">Image</option>
                <option value="audio">Audio</option>
              </select>
            </Field>
            <Field htmlFor="pre-file-name" label="File name">
              <input id="pre-file-name" name="file_name" className={fieldClass} required />
            </Field>
            <Field htmlFor="pre-mime" label="MIME type">
              <input id="pre-mime" name="mime_type" className={fieldClass} defaultValue="application/pdf" required />
            </Field>
            <Field htmlFor="pre-size" label="File size bytes">
              <input id="pre-size" name="file_size_bytes" className={fieldClass} type="number" min={1} required />
            </Field>
            <Field htmlFor="pre-checksum" label="Checksum SHA-256">
              <input id="pre-checksum" name="checksum_sha256" className={fieldClass} />
            </Field>
            {presignedMutation.isError ? <ErrorState title="Presigned upload failed" error={presignedMutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={presignedMutation.isPending}>
              Create upload URL
            </button>
          </form>
          {presignedMutation.data ? <div className="mt-4"><JsonPreview value={presignedMutation.data} /></div> : null}
        </Panel>

        <Panel title="Complete upload">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              completeMutation.mutate(event.currentTarget);
            }}
          >
            <Field htmlFor="complete-asset" label="Asset ID">
              <input id="complete-asset" name="asset_id" className={fieldClass} required />
            </Field>
            <Field htmlFor="complete-checksum" label="Checksum SHA-256">
              <input id="complete-checksum" name="checksum_sha256" className={fieldClass} />
            </Field>
            {completeMutation.isError ? <ErrorState title="Upload completion failed" error={completeMutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={completeMutation.isPending}>
              Complete upload
            </button>
          </form>
        </Panel>

        <Panel title="Proxy upload">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              proxyMutation.mutate(event.currentTarget);
            }}
          >
            <Field htmlFor="proxy-title" label="Title">
              <input id="proxy-title" name="title" className={fieldClass} required />
            </Field>
            <Field htmlFor="proxy-institution" label="Institution ID">
              <input id="proxy-institution" name="institution_id" className={fieldClass} defaultValue={context.profile.institution_id ?? ''} required />
            </Field>
            <Field htmlFor="proxy-type" label="Asset type">
              <select id="proxy-type" name="asset_type" className={fieldClass}>
                <option value="document">Document</option>
                <option value="video">Video</option>
                <option value="image">Image</option>
              </select>
            </Field>
            <Field htmlFor="proxy-file" label="File">
              <input
                id="proxy-file"
                className={fieldClass}
                type="file"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </Field>
            {proxyMutation.isError ? <ErrorState title="Proxy upload failed" error={proxyMutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={proxyMutation.isPending}>
              Upload file
            </button>
          </form>
        </Panel>
      </div>

      <div className="mt-5">
        {assetsQuery.isLoading ? <LoadingState label="Loading content assets" /> : null}
        {assetsQuery.isError ? <ErrorState error={assetsQuery.error} onRetry={() => void assetsQuery.refetch()} /> : null}
        {assetsQuery.data ? (
          <EntityList
            title="Recent assets"
            response={assetsQuery.data}
            detailKeys={['asset_type', 'status', 'owner_profile_id']}
            emptyMessage="No content assets yet."
          />
        ) : null}
      </div>
    </PortalLayout>
  );
}
