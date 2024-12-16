// app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './styles/globals.css'
import { ToastProvider } from './components/providers/toast-provider'


const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Video Summarizer',
  description: 'Transcribe and summarize videos',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-100`}>
        <div className="min-h-screen flex flex-col">
          <header className="bg-blue-600 text-white p-4 shadow-md">
            <div className="container mx-auto flex justify-between items-center">
              <h4 className="text-2xl font-bold">AI Video Summarizer</h4>
            </div>
          </header>
          <ToastProvider />          
          <main className="min-w-96 max-w-full flex-grow container mx-auto px-4 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
