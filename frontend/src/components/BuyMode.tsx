import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Bot, Upload, MessageCircle, Camera, Send } from 'lucide-react'

interface BuyModeProps {
  onBack: () => void
  onSavedClick: () => void
}

type BuyModeType = 'photo' | 'chat'

export function BuyMode({ onBack, onSavedClick }: BuyModeProps) {
  const [mode, setMode] = useState<BuyModeType>('photo')
  const [messages, setMessages] = useState([
    { type: 'bot', content: "Hi! I'm your AI home concierge. Upload a photo of your room and I'll help make it cozy! 🏡✨" }
  ])
  const [isUploading, setIsUploading] = useState(false)
  const [products, setProducts] = useState([])
  const [savedItems, setSavedItems] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([
    { type: 'bot', content: "Hi! I'm your AI home concierge. How can I help make your space more cozy today? 🏡✨" }
  ])
  const [isChatting, setIsChatting] = useState(false)

  // Load saved items on component mount
  useEffect(() => {
    loadSavedItems()
  }, [])

  const loadSavedItems = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/buy/saved-items/default_user')
      if (response.ok) {
        const data = await response.json()
        setSavedItems(data.saved_items || [])
      }
    } catch (error) {
      console.error('Error loading saved items:', error)
    }
  }

  const saveProduct = async (product: any) => {
    try {
      const response = await fetch('http://localhost:8000/api/buy/save-item', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'default_user',
          product: product
        }),
      })

      if (response.ok) {
        setMessages(prev => [...prev, {
          type: 'bot',
          content: `✅ Saved "${product.title}" to your saved items!`
        }])
        loadSavedItems()
      } else {
        throw new Error('Failed to save item')
      }
    } catch (error) {
      console.error('Error saving product:', error)
      setMessages(prev => [...prev, {
        type: 'bot',
        content: `❌ Sorry, couldn't save "${product.title}". Please try again.`
      }])
    }
  }

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setIsUploading(true)
      
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        setMessages(prev => [...prev, 
          { type: 'user', content: `Uploaded: ${file.name}` }
        ])
        
        const response = await fetch('http://localhost:8000/api/buy/analyze-room', {
          method: 'POST',
          body: formData,
        })
        
        if (!response.ok) {
          throw new Error('Failed to analyze room')
        }
        
        const data = await response.json()
        
        setMessages(prev => [...prev,
          { type: 'bot', content: data.message },
          { type: 'bot', content: `I can see this is a ${data.analysis.room_type}. ${data.analysis.overall_assessment}` },
          { type: 'bot', content: "Here are my top recommendations:" }
        ])
        
        data.analysis.suggestions.forEach((suggestion: any, index: number) => {
          setTimeout(() => {
            setMessages(prev => [...prev, {
              type: 'bot',
              content: `${index + 1}. **${suggestion.item}** - ${suggestion.description}`
            }])
          }, (index + 1) * 1000)
        })
        
        setProducts(data.products)
        
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'bot',
            content: `I found ${data.products.length} products that would be perfect for your space! Check them out below.`
          }])
        }, (data.analysis.suggestions.length + 1) * 1000)
        
      } catch (error) {
        console.error('Error analyzing room:', error)
        setMessages(prev => [...prev, {
          type: 'bot',
          content: "Sorry, I had trouble analyzing your room. Please try again or upload a different image."
        }])
      } finally {
        setIsUploading(false)
      }
    }
  }

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || isChatting) return

    const message = chatInput.trim()
    setChatInput('')
    setIsChatting(true)

    setChatMessages(prev => [...prev, { type: 'user', content: message }])

    try {
      const response = await fetch('http://localhost:8000/api/buy/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'default_user',
          message: message,
          conversation_history: chatMessages.slice(-10)
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setChatMessages(prev => [...prev, { type: 'bot', content: data.response }])
      } else {
        throw new Error('Failed to get response')
      }
    } catch (error) {
      console.error('Error sending chat message:', error)
      setChatMessages(prev => [...prev, {
        type: 'bot',
        content: "Sorry, I'm having trouble right now. Please try again!"
      }])
    } finally {
      setIsChatting(false)
    }
  }

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 30, stiffness: 300 }}
      className="min-h-screen flex flex-col"
    >
      {/* Header */}
      <header className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <button 
            onClick={onBack} 
            className="flex items-center text-white/60 hover:text-white transition-colors group"
          >
            <ArrowRight className="w-4 h-4 mr-2 rotate-180 transition-transform group-hover:-translate-x-1" />
            <span className="text-sm font-medium">Back to Home</span>
          </button>
          <div className="flex items-center space-x-6">
            <button
              onClick={onSavedClick}
              className="flex items-center text-white/60 hover:text-white transition-colors"
            >
              <span className="text-sm font-medium">
                Saved ({savedItems.length})
              </span>
            </button>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-blue-400" />
              </div>
              <span className="text-sm font-medium">Buy Mode — AI Assistant</span>
            </div>
          </div>
        </div>
      </header>

      {/* Mode Toggle */}
      <div className="p-6 border-b border-white/10">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => setMode('photo')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                mode === 'photo' 
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                  : 'text-white/60 hover:text-white hover:bg-white/5'
              }`}
            >
              <Camera className="w-4 h-4" />
              <span>Photo Analysis</span>
            </button>
            <button
              onClick={() => setMode('chat')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                mode === 'chat' 
                  ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' 
                  : 'text-white/60 hover:text-white hover:bg-white/5'
              }`}
            >
              <MessageCircle className="w-4 h-4" />
              <span>Chat Mode</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {mode === 'photo' ? (
        <main className="flex-1 flex-col max-w-4xl mx-auto w-full p-6">
          <div className="flex-1 space-y-6 mb-8 overflow-y-auto">
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-md px-6 py-4 rounded-2xl ${
                  message.type === 'user' 
                    ? 'bg-white text-black' 
                    : 'glass-card text-white'
                }`}>
                  <p className="text-body" dangerouslySetInnerHTML={{ 
                    __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
                  }} />
                </div>
              </motion.div>
            ))}
            
            {isUploading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="glass-card px-6 py-4 rounded-2xl">
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <span className="text-body text-white/80">Analyzing your room...</span>
                  </div>
                </div>
              </motion.div>
            )}
            
            {products.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <h3 className="text-heading text-xl text-white/80">Recommended Products</h3>
                <div className="grid gap-4">
                  {products.map((product: any, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="glass-card p-4 rounded-xl"
                    >
                      <div className="space-y-3">
                        <h4 className="text-body font-medium text-white">{product.title}</h4>
                        <p className="text-small text-white/60">{product.description}</p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className="text-small text-blue-400 capitalize">{product.category}</span>
                            <span className="text-small text-white/40">from {product.store}</span>
                          </div>
                          <div className="flex items-center space-x-3">
                            <button
                              onClick={() => saveProduct(product)}
                              className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-small hover:bg-blue-500/30 transition-colors"
                            >
                              💾 Save
                            </button>
                            <a 
                              href={product.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-small text-white/80 hover:text-white transition-colors"
                            >
                              View Product →
                            </a>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          <div className="glass-card rounded-2xl p-8">
            <label className="flex flex-col items-center justify-center h-40 border-2 border-dashed border-white/20 rounded-xl cursor-pointer hover:border-white/40 transition-colors group">
              <Upload className="w-8 h-8 text-white/40 mb-3 group-hover:text-white/60 transition-colors" />
              <span className="text-body text-white/60 mb-1">Upload a photo of your room</span>
              <span className="text-sm text-white/40">PNG, JPG up to 10MB</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </label>
          </div>
        </main>
      ) : (
        /* Chat Mode */
        <main className="flex-1 max-w-4xl mx-auto w-full p-6 flex flex-col">
          <div className="flex-1 glass-card rounded-2xl p-6 flex flex-col">
            <div className="flex-1 space-y-6 mb-6 overflow-y-auto max-h-[500px]">
              {chatMessages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-md px-6 py-4 rounded-2xl ${
                    message.type === 'user' 
                      ? 'bg-purple-500/20 text-purple-100 border border-purple-500/30' 
                      : 'bg-white/5 text-white border border-white/10'
                  }`}>
                    <p className="text-body" dangerouslySetInnerHTML={{ 
                      __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
                    }} />
                  </div>
                </motion.div>
              ))}
              
              {isChatting && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="bg-white/5 border border-white/10 px-6 py-4 rounded-2xl">
                    <div className="flex items-center space-x-3">
                      <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                      <span className="text-body text-white/80">Thinking...</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            <form onSubmit={handleChatSubmit} className="flex items-center space-x-3">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about home decoration, furniture, or specific products..."
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:border-purple-500/50 focus:bg-white/10 transition-colors"
                disabled={isChatting}
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || isChatting}
                className="bg-purple-500/20 hover:bg-purple-500/30 disabled:bg-white/5 disabled:text-white/30 text-purple-400 border border-purple-500/30 disabled:border-white/10 rounded-xl px-4 py-3 transition-colors flex items-center space-x-2"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </form>
          </div>
        </main>
      )}
    </motion.div>
  )
}
