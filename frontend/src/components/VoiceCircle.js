import React from "react";
import { motion } from "framer-motion";

export default function VoiceCircle({ listening, speaking }) {
  return (
    <div className="flex flex-col items-center">
      <motion.div
        animate={{
          scale: listening ? [1, 1.3, 1] : speaking ? [1, 1.2, 1] : 1,
          opacity: listening ? [0.8, 1, 0.8] : speaking ? [0.7, 1, 0.7] : 0.9,
        }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        className={`rounded-full w-32 h-32 flex items-center justify-center backdrop-blur-sm border-4 ${
          listening 
            ? "bg-red-500 bg-opacity-80 border-red-300 shadow-red-500/50" 
            : speaking 
            ? "bg-green-500 bg-opacity-80 border-green-300 shadow-green-500/50" 
            : "bg-blue-500 bg-opacity-80 border-blue-300 shadow-blue-500/50"
        } shadow-2xl`}
      >
        <span className="text-lg font-bold text-white text-center">
          {listening ? "🎙️\nListening" : speaking ? "🔊\nSpeaking" : "🤖\nActive"}
        </span>
      </motion.div>
      
      {/* Pulse rings */}
      <motion.div
        animate={{
          scale: [1, 2, 1],
          opacity: [0.6, 0, 0.6],
        }}
        transition={{ duration: 2, repeat: Infinity }}
        className={`absolute rounded-full w-32 h-32 border-2 ${
          listening ? "border-red-400" : speaking ? "border-green-400" : "border-blue-400"
        }`}
      />
      <motion.div
        animate={{
          scale: [1, 2.5, 1],
          opacity: [0.4, 0, 0.4],
        }}
        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
        className={`absolute rounded-full w-32 h-32 border-2 ${
          listening ? "border-red-400" : speaking ? "border-green-400" : "border-blue-400"
        }`}
      />
    </div>
  );
}
