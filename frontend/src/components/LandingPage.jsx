const FEATURES = [
  {
    icon: 'LAW',
    title: 'Legal answers',
    desc: 'Guidance grounded in Indian laws such as the DV Act, POSH and IPC 498A.',
  },
  {
    icon: 'DOC',
    title: 'FIR drafts',
    desc: 'Complaint drafts and next steps that are easier to read, edit and print.',
  },
  {
    icon: 'HELP',
    title: 'Nearby support',
    desc: 'Find One Stop Centres, helplines, shelters and legal aid offices.',
  },
  {
    icon: 'PLAN',
    title: 'Safety plan',
    desc: 'Personalised steps for safer decisions in urgent or sensitive situations.',
  },
]

const STEPS = [
  ['1', 'Ask in your language', 'Type or speak in Hindi, Bengali, Tamil and more.'],
  ['2', 'Get grounded answers', 'Receive simple explanations with useful legal context.'],
  ['3', 'Take action', 'Move to a draft, resource, helpline or safety plan when needed.'],
]

const LANGUAGES = [
  'English',
  'Hindi',
  'Bengali',
  'Tamil',
  'Telugu',
  'Marathi',
  'Gujarati',
  'Kannada',
  'Malayalam',
]

export default function LandingPage({ onStart }) {
  return (
    <main className="flex-1 overflow-y-auto">
      {/* hero */}
      <section className="bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-8
                        sm:px-6 sm:py-12 lg:grid-cols-[1.04fr_0.96fr]
                        lg:items-center lg:px-8 lg:py-16">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full
                            border border-emerald-200 bg-emerald-50 px-3 py-1.5
                            text-xs font-medium text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Free. No login. Always available.
            </div>

            <h1 className="mt-5 text-3xl font-semibold leading-tight
                           text-gray-950 sm:text-4xl lg:text-5xl">
              Legal support for women, in the language they trust.
            </h1>

            <p className="mt-4 max-w-xl text-sm leading-7 text-gray-600
                          sm:text-base">
              SakhiBot helps women understand rights, prepare complaint drafts,
              find emergency contacts and plan safer next steps across India.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onStart}
                className="inline-flex items-center justify-center rounded-2xl
                           bg-emerald-600 px-6 py-3.5 text-sm font-semibold
                           text-white shadow-sm transition-colors
                           hover:bg-emerald-700 focus:outline-none
                           focus:ring-2 focus:ring-emerald-400
                           focus:ring-offset-2"
              >
                Start asking
                <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24"
                  stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round"
                    strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>

              <a
                href="tel:181"
                className="inline-flex items-center justify-center rounded-2xl
                           border border-red-200 bg-white px-6 py-3.5 text-sm
                           font-semibold text-red-600 transition-colors
                           hover:bg-red-50"
              >
                <svg className="mr-2 h-4 w-4" fill="currentColor"
                  viewBox="0 0 24 24">
                  <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z" />
                </svg>
                Call 181 now
              </a>
            </div>

            <div className="mt-8 grid grid-cols-3 gap-3 text-center sm:max-w-lg">
              {[
                ['9+', 'Languages'],
                ['24/7', 'Access'],
                ['181', 'Helpline'],
              ].map(([value, label]) => (
                <div key={label} className="rounded-2xl border border-emerald-100
                                            bg-emerald-50/70 px-3 py-3">
                  <p className="text-lg font-semibold text-emerald-700">
                    {value}
                  </p>
                  <p className="mt-0.5 text-[11px] font-medium text-gray-500">
                    {label}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="overflow-hidden rounded-2xl border
                            border-emerald-100 bg-white shadow-xl">
              <div className="border-b border-emerald-100 bg-emerald-600
                              px-5 py-4 text-white">
                <p className="text-xs font-medium uppercase tracking-wide
                              text-emerald-100">
                  SakhiBot
                </p>
                <p className="mt-1 text-lg font-semibold">
                  Rights assistant preview
                </p>
              </div>
              <div className="space-y-4 p-5 sm:p-6">
                <div className="max-w-[86%] rounded-2xl rounded-tl-sm
                                bg-gray-100 px-4 py-3 text-sm leading-6
                                text-gray-700">
                  Tell me what happened. I can explain possible rights and
                  next steps in simple language.
                </div>
                <div className="ml-auto max-w-[82%] rounded-2xl rounded-tr-sm
                                bg-emerald-600 px-4 py-3 text-sm leading-6
                                text-white">
                  Can I file a complaint for workplace harassment?
                </div>
                <div className="max-w-[90%] rounded-2xl rounded-tl-sm
                                bg-gray-100 px-4 py-3 text-sm leading-6
                                text-gray-700">
                  Yes. The POSH Act protects women at workplaces. You can ask
                  the Internal Committee to begin an inquiry.
                </div>
                <div className="flex flex-wrap gap-2 pt-2">
                  {['Legal source', 'Draft complaint'].map(item => (
                    <span key={item} className="rounded-full border
                                                border-emerald-200 bg-emerald-50
                                                px-3 py-1.5 text-xs font-semibold
                                                text-emerald-700">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* features */}
      <section className="border-y border-emerald-100 bg-emerald-50/70">
        <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="mb-6 flex flex-col gap-2 sm:flex-row
                          sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide
                            text-emerald-700">
                What it covers
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-gray-950">
                Support from question to action
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-gray-600">
              Designed for quick answers, but broad enough for real situations:
              law, documents, resources and safety.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(feature => (
              <div key={feature.title}
                className="rounded-2xl border border-emerald-100 bg-white p-5
                           shadow-sm">
                <div className="flex h-10 w-10 items-center justify-center
                                rounded-xl bg-emerald-100 text-[10px]
                                font-bold text-emerald-700">
                  {feature.icon}
                </div>
                <h3 className="mt-4 text-sm font-semibold text-gray-900">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-gray-500">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* workflow and coverage */}
      <section className="bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-10
                        sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8 lg:py-14">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide
                          text-emerald-700">
              How it works
            </p>
            <div className="mt-5 space-y-5">
              {STEPS.map(([n, title, desc]) => (
                <div key={n} className="flex gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center
                                  justify-center rounded-full bg-emerald-100
                                  text-sm font-bold text-emerald-700">
                    {n}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900">
                      {title}
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-gray-500">
                      {desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-emerald-100 bg-white p-5
                            shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900">
                Language coverage
              </h3>
              <div className="mt-4 flex flex-wrap gap-2">
                {LANGUAGES.map(language => (
                  <span key={language}
                    className="rounded-full border border-emerald-200
                               bg-emerald-50 px-3 py-1.5 text-xs font-medium
                               text-emerald-700">
                    {language}
                  </span>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-red-100 bg-red-50 p-5">
              <h3 className="text-sm font-semibold text-red-800">
                Emergency access
              </h3>
              <p className="mt-2 text-sm leading-6 text-red-700">
                Fast links to 181, 100, 112 and NCW helpline can appear when
                urgent risk is detected.
              </p>
              <a href="tel:112"
                className="mt-4 inline-flex items-center justify-center
                           rounded-xl bg-white px-4 py-2.5 text-sm
                           font-semibold text-red-600 shadow-sm">
                Call 112
              </a>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
