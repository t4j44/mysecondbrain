import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Taj's Second Brain",
    short_name: 'Second Brain',
    description: 'Private AI operating system for ventures, relationships, tasks, and knowledge.',
    start_url: '/dashboard',
    scope: '/',
    display: 'standalone',
    background_color: '#0a0510',
    theme_color: '#12081d',
    orientation: 'portrait-primary',
    icons: [
      {
        src: '/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
        purpose: 'any',
      },
      {
        src: '/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
        purpose: 'maskable',
      },
    ],
  };
}
