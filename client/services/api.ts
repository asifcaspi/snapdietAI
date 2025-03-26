import * as FileSystem from 'expo-file-system';
import axios from 'axios';

const API_URL = 'http://172.20.10.4:8000/upload';

export const uploadImage = async (imageUri: string) => {
  try {
    // Convert the file URI to a base64 string
    
    const base64Image = await FileSystem.readAsStringAsync(imageUri, {
      encoding: FileSystem.EncodingType.Base64,
    });

    // Add the base64 prefix (e.g., for JPEG images)
    const base64WithPrefix = `data:image/jpeg;base64,${base64Image}`;

    // Send the base64 image to the server
    const response = await axios.post(API_URL, {
      image: base64WithPrefix,
    });

    return response.data;
  } catch (error) {
    console.error('Error uploading image:', error);
    throw error;
  }
};