import React from "react";
import { View, Text, Image, StyleSheet, FlatList, Button, ActivityIndicator } from "react-native";

interface ImageResultDisplayProps {
  imageUri: string;
  results: Record<string, string | null>;
  onReturn: () => void;
  loading: boolean; // Add loading prop
}

const ImageResultDisplay: React.FC<ImageResultDisplayProps> = ({ imageUri, results, onReturn, loading }) => {
  return (
    <View style={styles.container}>
      {/* Display the image */}
      <Image source={{ uri: imageUri }} style={styles.image} />

      {loading ? ( // Show loader when loading is true
        <ActivityIndicator size="large" color="#338859" />
      ) : (
        <>
          {/* Display the results */}
          <Text style={styles.resultsTitle}>Results:</Text>
          <FlatList
            data={Object.entries(results)}
            keyExtractor={([key]) => key}
            renderItem={({ item: [key, value] }) => (
              <Text style={styles.resultItem}>
                {key}: {value ? value + " cal" : "N/A"}
              </Text>
            )}
          />
        </>
      )}

      <Button title="Return to Camera" onPress={onReturn} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 20,
    alignItems: "center",
  },
  image: {
    width: 200,
    height: 200,
    resizeMode: "contain",
    marginBottom: 20,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  resultItem: {
    fontSize: 16,
    marginBottom: 5,
  },
});

export default ImageResultDisplay;