import React from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { ArrowRight, Sparkles, Camera, Video } from 'lucide-react'
import { StickyNavbar } from './Navbar'
import { ScrollReveal } from './ScrollReveal'

type AppMode = 'landing' | 'buy' | 'sell' | 'saved'

interface LandingPageProps {
  onModeSelect: (mode: AppMode) => void
}

export function LandingPage({ onModeSelect }: LandingPageProps) {
  const { scrollY } = useScroll()
  const y1 = useTransform(scrollY, [0, 500], [0, -100])
  const y2 = useTransform(scrollY, [0, 500], [0, -150])
  const opacity = useTransform(scrollY, [0, 300], [1, 0.3])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="relative min-h-screen"
    >
      {/* Background Elements */}
      <div className="fixed inset-0 grid-pattern opacity-40" style={{ pointerEvents: 'none' }} />
      <motion.div 
        style={{ y: y1, pointerEvents: 'none' }}
        className="fixed top-32 left-32 w-[500px] h-[500px] bg-blue-500/3 rounded-full blur-3xl animate-float"
      />
      <motion.div 
        style={{ y: y2, pointerEvents: 'none' }}
        className="fixed bottom-32 right-32 w-[500px] h-[500px] bg-purple-500/3 rounded-full blur-3xl animate-float-delayed"
      />

      {/* Navigation */}
      <StickyNavbar>
        <div className="container-width flex items-center justify-between">
          <motion.div 
            className="flex items-center space-x-4"
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div 
              className="w-10 h-10 bg-white rounded-full flex items-center justify-center micro-interaction"
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <Sparkles className="w-5 h-5 text-black" />
            </motion.div>
            <span className="text-2xl font-medium tracking-tight text-heading">SmartScape</span>
          </motion.div>
          
          <div className="hidden md:flex items-center space-x-12 text-small">
            <motion.a 
              href="#" 
              className="text-white/60 hover:text-white transition-colors duration-300 micro-interaction"
              whileHover={{ y: -2 }}
            >
              Features
            </motion.a>
            <motion.a 
              href="#" 
              className="text-white/60 hover:text-white transition-colors duration-300 micro-interaction"
              whileHover={{ y: -2 }}
            >
              About
            </motion.a>
            <motion.a 
              href="#" 
              className="text-white/60 hover:text-white transition-colors duration-300 micro-interaction"
              whileHover={{ y: -2 }}
            >
              Contact
            </motion.a>
          </div>
        </div>
      </StickyNavbar>

      {/* Hero Section */}
      <section className="scroll-section scroll-highlight">
        <motion.div style={{ opacity }} className="container-width text-center">
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-12"
          >
            <div className="space-y-8">
              <motion.h1 
                className="hero-text text-display text-shadow"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8, duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
              >
                Your AI-Powered
                <br />
                <motion.span 
                  className="gradient-accent"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.2, duration: 1 }}
                >
                  Home Concierge
                </motion.span>
              </motion.h1>
              
              <motion.p 
                className="text-body text-white/70 max-w-4xl mx-auto text-xl leading-relaxed stagger-animation"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.4, duration: 0.8 }}
              >
                Transform your space with zero effort. Whether you're decluttering to sell 
                or making your room cozy, SmartScape's autonomous agents handle everything.
              </motion.p>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.6, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-8 relative z-10"
            >
              <motion.button 
                className="btn-primary group relative z-20"
                whileHover={{ scale: 1.05, y: -3 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => onModeSelect('buy')}
                style={{ pointerEvents: 'auto' }}
              >
                Get Started
              </motion.button>
              <motion.a 
                href="https://youtu.be/NUEluIMwpCk"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary relative z-20"
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                style={{ pointerEvents: 'auto' }}
              >
                Watch Demo
              </motion.a>
            </motion.div>
          </motion.div>
        </motion.div>
      </section>

      {/* Mode Selection */}
      <section className="relative section-padding">
        <div className="container-width">
          <ScrollReveal>
            <div className="text-center mb-32">
              <motion.h2 
                className="text-display text-6xl mb-6"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                viewport={{ once: true }}
              >
                Two ways to transform
              </motion.h2>
              <motion.p 
                className="text-body text-white/50 max-w-2xl mx-auto"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.8 }}
                viewport={{ once: true }}
              >
                Choose your path to a better space
              </motion.p>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Buy Mode */}
            <ScrollReveal delay={0.1}>
              <motion.div
                whileHover={{ y: -8, scale: 1.02 }}
                onClick={() => onModeSelect('buy')}
                className="group cursor-pointer"
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="glass-card p-10 h-full transition-all duration-300 group-hover:border-white/10">
                  <div className="space-y-6">
                    <motion.div 
                      className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300"
                      whileHover={{ scale: 1.1 }}
                    >
                      <Camera className="w-8 h-8 text-white/80" />
                    </motion.div>
                    
                    <div className="space-y-4">
                      <h3 className="text-heading text-2xl">Buy</h3>
                      <p className="text-body text-white/60 leading-relaxed">
                        Upload a photo of your room and get AI-powered suggestions to make it cozy.
                      </p>
                    </div>
                    
                    <motion.div 
                      className="flex items-center text-white/60 group-hover:text-white transition-colors pt-4"
                      whileHover={{ x: 4 }}
                    >
                      <span className="text-small">Make it cozy</span>
                      <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            </ScrollReveal>

            {/* Sell Mode */}
            <ScrollReveal delay={0.2}>
              <motion.div
                whileHover={{ y: -8, scale: 1.02 }}
                onClick={() => onModeSelect('sell')}
                className="group cursor-pointer"
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="glass-card p-10 h-full transition-all duration-300 group-hover:border-white/10">
                  <div className="space-y-6">
                    <motion.div 
                      className="w-16 h-16 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300"
                      whileHover={{ scale: 1.1 }}
                    >
                      <Video className="w-8 h-8 text-white/80" />
                    </motion.div>
                    
                    <div className="space-y-4">
                      <h3 className="text-heading text-2xl">Sell</h3>
                      <p className="text-body text-white/60 leading-relaxed">
                        Upload a video of your space and let AI identify sellable items.
                      </p>
                    </div>
                    
                    <motion.div 
                      className="flex items-center text-white/60 group-hover:text-white transition-colors pt-4"
                      whileHover={{ x: 4 }}
                    >
                      <span className="text-small">Declutter space</span>
                      <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative section-padding border-t border-white/5">
        <div className="container-width text-center">
          <motion.p 
            className="text-white/40 text-small"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            © 2024 SmartScape — Powered by AI, designed for you
          </motion.p>
        </div>
      </footer>

    </motion.div>
  )
}
