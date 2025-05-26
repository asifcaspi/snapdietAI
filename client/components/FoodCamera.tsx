import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import * as ImageManipulator from 'expo-image-manipulator';
import { useRef, useState } from 'react';
import { Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { uploadImage } from '../services/api';
import ImageResultDisplay from './ImageResultDisplay';

export default function FoodCamera() {
  const [facing, setFacing] = useState<CameraType>("back");
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, string | null>>({});
  const [loading, setLoading] = useState(false);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant Permission" />
      </View>
    );
  }

  const fixOrientation = async (imageUri: string) => {
    const fixedImage = await ImageManipulator.manipulateAsync(imageUri, [], {
      compress: 1,
      format: ImageManipulator.SaveFormat.JPEG,
    });
    return fixedImage.uri;
  };

  const takePicture = async () => {
    const photo = await cameraRef.current?.takePictureAsync();
    if (photo) {
      const fixedUri = await fixOrientation(photo.uri);
      setImageUri(fixedUri); // Save the image URI to display later
      setLoading(true); // Set loading to true while uploading

      try {
        const response = await uploadImage(fixedUri);
        setResults(response); // Save the results to display below the image
      } catch (error) {
        console.error("Error uploading image:", error);
      } finally {
        setLoading(false); // Reset loading state
      }
    }
  };

  const handleReturn = () => {
    setImageUri(null); // Reset the image URI
    setResults({}); // Reset the results
  };

  return (
    <View style={styles.container}>
      <View>
        <CameraView style={[styles.camera, imageUri && styles.hidden]} ref={cameraRef} facing={facing}>
        </CameraView>
        <View
          style={[
            styles.overlay,
            imageUri && { opacity: 0, pointerEvents: 'none' }
          ]}
        >
          <View style={styles.circle}></View>
          <View style={styles.coinCircle}></View>
        </View>
      </View>
      {!imageUri ? (
        <>
          <View style={styles.buttonContainer}>
            <TouchableOpacity style={styles.takePictureButton} onPress={takePicture}>
              <Text style={styles.text}>Take Picture</Text>
            </TouchableOpacity>
          </View>
        </>
      ) : (
        <ImageResultDisplay imageUri={imageUri} results={results} loading={loading} onReturn={handleReturn} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    // width: '90%',
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
  },
  camera: {
    // flex: 1,
    width: 300, // Set a fixed width
    height: 300, // Set the same height to make it a square
    alignSelf: 'center',
    position: 'relative'
  },
  hidden: {
    display: 'none',
  },
  noColor: {
    borderColor: 'transparent',
  },
  overlay: {
    position: 'absolute',
    top: '50%',
    width: 300,
    height: 300,
    zIndex: 2,
    transform: [{ translateY: -150 }],
    display: 'flex',
    pointerEvents: 'none',
  },
  circle: {
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 2,
    borderColor: 'white',
    borderStyle: 'dashed',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -100 }, { translateY: -100}]
  },
  coinCircle:{
    width: 40,
    height: 40,
    borderRadius: 100,
    borderWidth: 2,
    borderColor: 'white',
    borderStyle: 'dashed',
    position: 'relative',
    top: 20,
    left: 30,
  },
  buttonContainer: {
    marginTop: 10,
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  takePictureButton: {
    width: 200,
    alignSelf: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'rgba(51, 136, 89, 0.7)',
    borderRadius: 50,
  },
});
