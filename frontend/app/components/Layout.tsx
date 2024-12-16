// components/Layout.tsx
import React, { ReactNode } from 'react';
import Head from 'next/head';

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, 
  title = 'Video Summarizer' 
}) => {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="Transcribe and summarize videos" />
        <link rel="icon" href="/favicon.ico" />
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      
      <div className="min-h-screen flex flex-col">
        <header className="bg-blue-600 text-white p-4 shadow-md">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">Video Summarizer</h1>
          </div>
        </header>
        
        <main className="flex-grow container mx-auto px-4 py-6">
          {children}
        </main>
      
      </div>
    </>
  );
};

export default Layout;
