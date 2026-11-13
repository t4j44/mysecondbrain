import { test as base } from '@playwright/test';
import { configurePreviewAccess } from './helpers/preview-access';

export const test = base.extend({
  context: async ({ context }, provideContext) => {
    await configurePreviewAccess(context);
    await provideContext(context);
  },
});
export { expect } from '@playwright/test';
