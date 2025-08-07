import React, { useRef, useEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import * as THREE from 'three';

interface ModelLoaderProps {
  result: {
    modelUrl: string;
    metadata?: {
      vertices?: number;
      faces?: number;
      boundingBox?: {
        min: [number, number, number];
        max: [number, number, number];
      };
    };
  };
}

const ModelLoader: React.FC<ModelLoaderProps> = ({ result }) => {
  const meshRef = useRef<THREE.Points>(null);
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!result?.modelUrl) {
      setError('No model URL provided');
      setLoading(false);
      return;
    }

    const loader = new PLYLoader();
    setLoading(true);
    setError(null);

    loader.load(
      result.modelUrl,
      (geometry: THREE.BufferGeometry) => {
        console.log('PLY loaded successfully:', geometry);
        
        // 计算几何体的边界框
        geometry.computeBoundingBox();
        geometry.computeVertexNormals();
        
        // 如果没有颜色属性，添加默认颜色
        if (!geometry.attributes.color) {
          const colors = new Float32Array(geometry.attributes.position.count * 3);
          for (let i = 0; i < colors.length; i += 3) {
            colors[i] = 0.8;     // R
            colors[i + 1] = 0.8; // G
            colors[i + 2] = 0.8; // B
          }
          geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        }
        
        setGeometry(geometry);
        setLoading(false);
      },
      (progress: ProgressEvent) => {
        console.log('Loading progress:', (progress.loaded / progress.total * 100) + '%');
      },
      (error: unknown) => {
        console.error('Error loading PLY:', error);
        setError('Failed to load 3D model');
        setLoading(false);
      }
    );

    return () => {
      // 清理资源
      if (geometry) {
        geometry.dispose();
      }
    };
  }, [result?.modelUrl]);

  // 旋转动画
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.1;
    }
  });

  if (loading) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="#888888" wireframe />
      </mesh>
    );
  }

  if (error || !geometry) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="#ff0000" wireframe />
      </mesh>
    );
  }

  return (
    <points ref={meshRef}>
      <bufferGeometry attach="geometry" {...geometry} />
      <pointsMaterial
        attach="material"
        vertexColors
        size={0.02}
        sizeAttenuation={true}
      />
    </points>
  );
};

export default ModelLoader;