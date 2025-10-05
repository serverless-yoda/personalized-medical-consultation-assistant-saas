import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <title>Personalized Medical Consultation Assistant</title>
        <meta name="description" content="AI Driven Intelligent Summaries for Better Patient Care" />
      </Head>
      <body>
        <script
          // Immediately set .dark class based on preference (prevents FOUC)
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  if (
                    localStorage.getItem('theme') === 'dark' ||
                    (!localStorage.getItem('theme') &&
                      window.matchMedia('(prefers-color-scheme: dark)').matches)
                  ) {
                    document.documentElement.classList.add('dark')
                  } else {
                    document.documentElement.classList.remove('dark')
                  }
                } catch (e) {}
              })()
            `,
          }}
        />
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
