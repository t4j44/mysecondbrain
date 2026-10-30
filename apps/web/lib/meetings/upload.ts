import { env } from '@/lib/env';
import type { UploadAuthorization } from './types';
export interface AudioUploadClient { upload(blob: Blob, authorization: UploadAuthorization, token: string, progress: (percent: number) => void): Promise<void> }
export class BrowserAudioUploadClient implements AudioUploadClient {
  upload(blob: Blob, authorization: UploadAuthorization, token: string, progress: (percent: number) => void) {
    if (blob.size > authorization.max_bytes) return Promise.reject(new Error(`Recording is too large (maximum ${Math.floor(authorization.max_bytes / 1048576)} MB).`));
    return new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest(); const base = env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '');
      xhr.open('PUT', authorization.upload_url || `${base}${authorization.local_upload_endpoint}`);
      xhr.setRequestHeader('Content-Type', authorization.mime_type);
      if (!authorization.upload_url) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.upload.onprogress = e => { if (e.lengthComputable) progress(Math.round(e.loaded / e.total * 100)); };
      xhr.onload = () => { if ((xhr.status >= 200 && xhr.status < 300) || xhr.status === 409) resolve(); else reject(new Error("Couldn't upload this recording. Your copy is saved on this device. Retry.")); };
      xhr.onerror = () => reject(new Error('Connection lost. Your recording is saved on this device. Retry.'));
      xhr.timeout = 180000; xhr.ontimeout = xhr.onerror; xhr.send(blob);
    });
  }
}
