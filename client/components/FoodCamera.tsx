import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import * as ImageManipulator from 'expo-image-manipulator';
import { useRef, useState } from 'react';
import { Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { uploadImage } from '../services/api';

export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);

  if (!permission) {
    // Camera permissions are still loading.
    return <View />;
  }

  if (!permission.granted) {
    // Camera permissions are not granted yet.
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  const fixOrientation = async (imageUri: string) => {
    const fixedImage = await ImageManipulator.manipulateAsync(
      imageUri,
      [],
      { compress: 1, format: ImageManipulator.SaveFormat.JPEG }
    );
    return fixedImage.uri;
  };
  
  const takePicture = async () => {
    const photo = await cameraRef.current?.takePictureAsync();
    if (photo) {
      const fixedUri = await fixOrientation(photo.uri);
      await uploadImage(fixedUri);
    }
  };

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} ref={cameraRef} facing={facing}>
        <View style={styles.circle}>
        </View>
      </CameraView>
      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.takePictureButton} onPress={takePicture}>
          <Text style={styles.text}>Take Picture</Text>
        </TouchableOpacity>
      </View>
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
