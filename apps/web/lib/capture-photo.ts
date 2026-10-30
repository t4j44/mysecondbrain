export type CapturePhoto = { requestId: string; kind: 'business_card' | 'moment'; blob: Blob; preview: string };

export function fitPhoto(width: number, height: number, edge = 1600) {
  if (width <= 0 || height <= 0 || !Number.isFinite(width + height)) throw new Error('Invalid photo dimensions.');
  const scale = Math.min(1, edge / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}

export async function compressCapturePhoto(file: File): Promise<Blob> {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 8 * 1024**2) {
    throw new Error('Choose a JPG, PNG or WebP photo up to 8 MB.');
  }
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  try {
    if (bitmap.width * bitmap.height > 16000000) throw new Error('Choose a photo smaller than 16 megapixels.');
    const canvas = document.createElement('canvas');
    const size = fitPhoto(bitmap.width, bitmap.height);
    canvas.width = size.width; canvas.height = size.height;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Photo processing is unavailable. You can still type your note.');
    context.fillStyle = '#fff'; context.fillRect(0, 0, size.width, size.height);
    context.drawImage(bitmap, 0, 0, size.width, size.height);
    const encode = (type: string, quality: number) => new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Could not compress photo.')), type, quality));
    let blob = await encode('image/webp', .84);
    const type = blob.type === 'image/webp' ? 'image/webp' : 'image/jpeg';
    if (blob.type !== type) blob = await encode(type, .84);
    for (const quality of [.74, .64, .54]) {
      if (blob.size <= 500 * 1024) break;
      blob = await encode(type, quality);
    }
    if (blob.size > 2 * 1024**2) throw new Error('Photo is still too large. Try a smaller crop.');
    return blob;
  } finally { bitmap.close(); }
}
