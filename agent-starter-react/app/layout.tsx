import * as React from 'react';
import { headers } from 'next/headers';
import { getAppConfig } from '@/lib/utils';
import { Provider } from '@/components/provider';
import './globals.css'; 
import '@livekit/components-styles';

// This MUST be "export default"
export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return (
    <html lang="en">
      <body className="bg-black antialiased overflow-hidden">
        {/* Provider is critical for Jarvis to connect to the AI server */}
        <Provider appConfig={appConfig}>
          <main className="h-screen w-full">
            {children}
          </main>
        </Provider>
      </body>
    </html>
  );
}