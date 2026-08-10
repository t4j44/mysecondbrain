import * as React from 'react';
import { LoadingState } from '@/components/shared/loading-state';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';

export default function RootLoading() {
  return (
    <ResponsivePageContainer className="py-6">
      <LoadingState rows={2} showHeader={true} />
    </ResponsivePageContainer>
  );
}
