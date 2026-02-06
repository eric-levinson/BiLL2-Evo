'use client'

import { motion } from 'framer-motion'
import React from 'react'

const EXAMPLE_PROMPTS = [
  'Show me the top 10 dynasty WR rankings',
  'Compare Bijan Robinson vs Jahmyr Gibbs rushing stats for 2024',
  'What are the trending players on Sleeper this week?',
  'Analyze my Sleeper league rosters'
]

interface ExamplePromptButtonProps {
  text: string
  onClick: () => void
}

const ExamplePromptButton = ({ text, onClick }: ExamplePromptButtonProps) => {
  const baseStyles =
    'px-4 py-2 text-sm transition-colors font-dmmono tracking-tight border border-border hover:bg-neutral-800 rounded-xl cursor-pointer'

  return (
    <button onClick={onClick} className={baseStyles}>
      {text}
    </button>
  )
}

const ChatBlankState = () => {
  const handlePromptClick = (prompt: string) => {
    // TODO: Implement prompt injection when chat input is wired
    console.log('Selected prompt:', prompt)
  }

  return (
    <section
      className="flex flex-col items-center text-center font-geist"
      aria-label="Welcome message"
    >
      <div className="flex max-w-3xl flex-col gap-y-8">
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-3xl font-[600] tracking-tight"
        >
          <div className="flex items-center justify-center gap-x-2 whitespace-nowrap font-medium">
            <span className="flex items-center font-[600]">
              Welcome to BiLL-2 Evo
            </span>
          </div>
          <p className="mt-4 text-base font-normal text-neutral-400">
            Your AI-powered fantasy football analytics platform
          </p>
          <p className="mt-2 text-sm font-normal text-neutral-500">
            Get advanced NFL stats, Sleeper league insights, and dynasty rankings
          </p>
        </motion.h1>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex flex-col gap-3"
        >
          <p className="text-sm font-medium text-neutral-400">
            Try these example prompts:
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <ExamplePromptButton
                key={prompt}
                text={prompt}
                onClick={() => handlePromptClick(prompt)}
              />
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default ChatBlankState
