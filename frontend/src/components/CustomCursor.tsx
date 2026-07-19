'use client';
import React, { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

const CustomCursor = () => {
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);

  const springConfig = { damping: 25, stiffness: 300, mass: 0.8 };
  const lensXSpring = useSpring(cursorX, springConfig);
  const lensYSpring = useSpring(cursorY, springConfig);

  const [isHovering, setIsHovering] = useState(false);
  const [isTargeting, setIsTargeting] = useState(false);
  const [eggState, setEggState] = useState('normal');

  useEffect(() => {
    const handleEgg = (e: any) => {
      if (e.detail && typeof e.detail === 'object') {
        setEggState(e.detail.state);
      } else {
        setEggState(e.detail);
      }
    };
    window.addEventListener('EASTER_EGG', handleEgg);
    return () => window.removeEventListener('EASTER_EGG', handleEgg);
  }, []);

  useEffect(() => {
    const moveCursor = (e: MouseEvent) => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);

      const target = e.target as HTMLElement;
      if (
        target.tagName.toLowerCase() === 'a' ||
        target.tagName.toLowerCase() === 'button' ||
        target.closest('a') ||
        target.closest('button') ||
        target.classList.contains('nav-link') ||
        target.classList.contains('btn') ||
        target.closest('.cursor-pointer') ||
        window.getComputedStyle(target).cursor === 'pointer'
      ) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };

    window.addEventListener('mousemove', moveCursor);
    return () => {
      window.removeEventListener('mousemove', moveCursor);
    };
  }, [cursorX, cursorY]);

  if (typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches) {
    return null;
  }

  return (
    <>
      {/* Outer glow ring */}
      <motion.div
        animate={{
          scale: (eggState === 'suck' || eggState === 'supernova_charge') ? 0.8 : (isHovering ? 1.5 : 1),
          opacity: (eggState === 'suck' || eggState === 'supernova_charge') ? 0 : 1,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        style={{
          position: 'fixed',
          left: -25,
          top: -25,
          width: 50,
          height: 50,
          borderRadius: '50%',
          backdropFilter: 'blur(2px) contrast(1.8) brightness(1.1) saturate(1.2)',
          WebkitBackdropFilter: 'blur(2px) contrast(1.8) brightness(1.1) saturate(1.2)',
          border: '1px solid rgba(255, 255, 255, 0.4)',
          boxShadow: 'inset 0px 4px 10px rgba(255, 255, 255, 0.5), inset 0px -4px 10px rgba(0, 0, 0, 0.5), 0px 10px 20px rgba(0, 0, 0, 0.6)',
          pointerEvents: 'none',
          zIndex: 9997,
          x: lensXSpring,
          y: lensYSpring,
        }}
      />

      {/* Core dot */}
      <motion.div
        animate={{
          width: (eggState === 'supernova_explode' || eggState === 'supernova_charge') ? 100 : (eggState === 'suck' ? 48 : (isHovering ? 10 : 4)),
          height: (eggState === 'supernova_explode' || eggState === 'supernova_charge') ? 100 : (eggState === 'suck' ? 48 : (isHovering ? 10 : 4)),
          left: (eggState === 'supernova_explode' || eggState === 'supernova_charge') ? -50 : (eggState === 'suck' ? -24 : (isHovering ? -5 : -2)),
          top: (eggState === 'supernova_explode' || eggState === 'supernova_charge') ? -50 : (eggState === 'suck' ? -24 : (isHovering ? -5 : -2)),
          backgroundColor: (eggState === 'supernova_explode' || eggState === 'supernova_charge') ? '#ffffff' : (eggState === 'suck' ? 'rgba(0, 0, 0, 0.7)' : (isHovering ? 'rgba(255, 255, 255, 1)' : 'rgba(212, 212, 212, 1)')),
          boxShadow: (eggState === 'supernova_explode' || eggState === 'supernova_charge') ? '0 0 50px rgba(255,255,255,1), 0 0 150px rgba(255,255,255,0.9)' : (eggState === 'suck' ? 'inset 0px 4px 10px rgba(255, 255, 255, 0.4), inset 0px -4px 10px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(255, 255, 255, 0.8), 0 0 20px rgba(255, 255, 255, 0.6)' : 'inset 0px 0px 0px rgba(255,255,255,0), 0 0 10px rgba(255, 255, 255, 0.8)')
        }}
        transition={{ duration: eggState === 'supernova_explode' ? 0.3 : (eggState === 'supernova_charge' ? 2.0 : (eggState === 'suck' ? 1.0 : 0.2)), ease: 'easeOut' }}
        style={{
          position: 'fixed',
          borderRadius: '50%',
          backdropFilter: 'blur(4px) contrast(1.2)',
          WebkitBackdropFilter: 'blur(4px) contrast(1.2)',
          pointerEvents: 'none',
          zIndex: 9999,
          x: cursorX,
          y: cursorY,
        }}
      />
    </>
  );
};

export default CustomCursor;
