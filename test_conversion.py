from converter import convert_mp3_to_mp4
import os

def test_local_conversion():
    input_mp3 = "/home/adnanxpkd/drive_record_1763097786.mp3"
    output_mp4 = "test_output.mp4"
    
    if not os.path.exists(input_mp3):
        print(f"Error: Input file {input_mp3} not found.")
        return

    print(f"Starting conversion of {input_mp3}...")
    success = convert_mp3_to_mp4(input_mp3, output_mp4)
    
    if success and os.path.exists(output_mp4):
        print(f"Success! Output saved to {output_mp4}")
        # Clean up
        os.remove(output_mp4)
    else:
        print("Conversion failed.")

if __name__ == "__main__":
    test_local_conversion()
