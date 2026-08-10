'use client';

import * as React from 'react';
import { ErrorState } from '@/components/shared/error-state';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    console.error('Runtime Root Route Error:', error);
  }, [error]);

  return (
    <ResponsivePageContainer className="py-16">
      <ErrorState
        title="UNHANDLED ROUTE SEGMENT EXCEPTION"
        message="A catastrophic state error occurred within this route module. Access execution intercepted."
        error={{
          message: error.message,
          code: error.digest ? `DIGEST_${error.digest}` : 'ERR_ROUTE',
        }}
        onRetry={() => reset()}
      />
    </ResponsivePageContainer>
  );
}
