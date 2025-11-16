import json
from PIL import Image, ImageDraw, ImageFont

# JSON data
json_data = '''
{
  "walls": [
    {
      "wall_id": "wall_1",
      "start_point": {
        "x": 45.12345678,
        "y": 135.87654321
      },
      "end_point": {
        "x": 45.12345678,
        "y": 797.65432109
      }
    },
    {
      "wall_id": "wall_2",
      "start_point": {
        "x": 45.12345678,
        "y": 797.65432109
      },
      "end_point": {
        "x": 957.23456789,
        "y": 797.65432109
      }
    },
    {
      "wall_id": "wall_3",
      "start_point": {
        "x": 957.23456789,
        "y": 797.65432109
      },
      "end_point": {
        "x": 957.23456789,
        "y": 135.87654321
      }
    },
    {
      "wall_id": "wall_4",
      "start_point": {
        "x": 957.23456789,
        "y": 135.87654321
      },
      "end_point": {
        "x": 45.12345678,
        "y": 135.87654321
      }
    },
    {
      "wall_id": "wall_5",
      "start_point": {
        "x": 45.12345678,
        "y": 466.7654321
      },
      "end_point": {
        "x": 501.18765432,
        "y": 466.7654321
      }
    },
    {
      "wall_id": "wall_6",
      "start_point": {
        "x": 501.18765432,
        "y": 135.87654321
      },
      "end_point": {
        "x": 501.18765432,
        "y": 350.23456789
      }
    },
    {
      "wall_id": "wall_7",
      "start_point": {
        "x": 501.18765432,
        "y": 583.2956789
      },
      "end_point": {
        "x": 501.18765432,
        "y": 797.65432109
      }
    },
    {
      "wall_id": "wall_8",
      "start_point": {
        "x": 501.18765432,
        "y": 466.7654321
      },
      "end_point": {
        "x": 957.23456789,
        "y": 466.7654321
      }
    }
  ],
  "rooms": [
    {
      "room_name": "BEDROOM",
      "center_point": {
        "x": 273.17901235,
        "y": 301.32098765
      }
    },
    {
      "room_name": "LIVING",
      "center_point": {
        "x": 729.21111111,
        "y": 301.32098765
      }
    },
    {
      "room_name": "OFFICE",
      "center_point": {
        "x": 273.17901235,
        "y": 632.22530864
      }
    },
    {
      "room_name": "OFFICE",
      "center_point": {
        "x": 729.21111111,
        "y": 632.22530864
      }
    }
  ]
}
'''

# Parse JSON
data = json.loads(json_data)

# Create image with padding
padding = 50
width = 1100
height = 900

# Create white background
img = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(img)

# Draw walls
for wall in data['walls']:
    start_x = wall['start_point']['x']
    start_y = wall['start_point']['y']
    end_x = wall['end_point']['x']
    end_y = wall['end_point']['y']
    
    draw.line([(start_x, start_y), (end_x, end_y)], fill='black', width=3)

# Draw rooms with labels
try:
    font = ImageFont.truetype("arial.ttf", 20)
except:
    font = ImageFont.load_default()

for room in data['rooms']:
    x = room['center_point']['x']
    y = room['center_point']['y']
    name = room['room_name']
    
    # Draw a small circle at center
    radius = 5
    draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)], fill='red')
    
    # Draw room name
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text((x - text_width/2, y - text_height/2 - 15), name, fill='blue', font=font)

# Save image
img.save('floor_plan.png')
print("Image saved as 'floor_plan.png'")

# Display image (optional)
img.show()