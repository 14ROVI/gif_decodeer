from PIL import Image ## only used for displaying the image at the end (to check if it worked)

BASE64_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
width = None
height = None
background_colour_index = None
background_colour = None
num_global_colours = 0
global_colours = []
num_local_colours = 0
local_colours = []
end_of_file = False
cursor = 0
loop_times = -1


# helper functions
def decimal_to_string(n: int) -> str: # max value is 63 for my use case
    s = ""
    if n >= 32:
        s += "1"
        n = n - 32
    else:
        s += "0"
    if n >= 16:
        s += "1"
        n = n - 16
    else:
        s += "0"
    if n >= 8:
        s += "1"
        n = n - 8
    else:
        s += "0"
    if n >= 4:
        s += "1"
        n = n - 4
    else:
        s += "0"
    if n >= 2:
        s += "1"
        n = n - 2
    else:
        s += "0"
    if n >= 1:
        s += "1"
        n = n - 1
    else:
        s += "0"
    return s

def little_binary_to_decimal(s: str) -> int:
    s1 = s[:8]
    s2 = s[8:]
    return binary_to_decimal(s1) + binary_to_decimal(s2) * 2**8

def binary_to_decimal(s: str) -> int:
    val = 0
    for c in range(len(s)):
        val += 2**(len(s)-c-1) if s[c] == "1" else 0
    return val


# first decoder function
def base64_to_binary(text: str) -> str:
    decimal_values = (BASE64_TABLE.index(c) for c in text)
    return "".join(decimal_to_string(d) for d in decimal_values)


# gif decodeer functions
def decode_logical_screen_descriptor(binary_data):
    global width
    global height
    global background_colour_index
    global num_global_colours

    width = binary_data[0:2*8]
    height = binary_data[2*8:4*8]
    packet_field = binary_data[4*8:5*8]
    background_colour_index = binary_data[5*8:6*8]
    width = little_binary_to_decimal(width)
    height = little_binary_to_decimal(height)
    print(f"Width: {width}")
    print(f"Height: {height}")

    if packet_field[0] == "1":
        num_global_colours = 2 ** (binary_to_decimal(packet_field[5:8]) + 1)
        background_colour_index = binary_to_decimal(background_colour_index)
        print(f"BG index: {background_colour_index}")
        print(f"Colours: {num_global_colours}")

def decode_global_colour_table(binary_data):
    global global_colours

    for i in range(0, num_global_colours*3*8, 3*8):
        r = binary_to_decimal(binary_data[i: i+8])
        g = binary_to_decimal(binary_data[i+8: i+8*2])
        b = binary_to_decimal(binary_data[i+8*2: i+8*3])
        global_colours.append(
            (r, g, b)
        )
    print(f"BG colour: {global_colours[background_colour_index]}")


# start
with open("base64.txt", encoding="utf-8-sig") as file:
    text = file.read()
    text = text.replace("\n", "").replace("=", "").replace("\r", "")
    # base64 to binary
    binary_data = base64_to_binary(text)

    # we know it is a gif so remove the first 6 bytes
    binary_data = binary_data[8*6:] 

    # Logical screen descriptor
    logical_screen_descriptor = binary_data[:7*8]
    decode_logical_screen_descriptor(logical_screen_descriptor)
    binary_data = binary_data[7*8:]
    
    # global colour table
    global_colour_table = binary_data[:num_global_colours*3*8]
    decode_global_colour_table(global_colour_table)
    binary_data = binary_data[num_global_colours*3*8:]

    with Image.new("RGB", (width, height)) as img:

        while not end_of_file:
            # check extension 

            #if comment then skip over
            if binary_data[cursor:cursor+16] == "0010000111111110":
                length = binary_to_decimal(binary_data[cursor+16:cursor+24])
                cursor += 24 + length*8 + 8
                continue

            # if plain text then skip 
            elif binary_data[cursor:cursor+16] == "0010000100000001":
                cursor = cursor + 24
                while binary_data[cursor] != "00000000":
                    length = binary_to_decimal(binary_data[cursor:cursor+8])
                    cursor += length*8 + 8
                continue
            
            # if application extension then parse it into useful data
            elif binary_data[cursor:cursor+16] == "0010000111111111":
                cursor += 16
                length = binary_to_decimal(binary_data[cursor:cursor+8])
                cursor += length*8 + 8 + 16
                loop_times = little_binary_to_decimal(binary_data[cursor:cursor+16])
                cursor += 24
                continue
            
            # if end of file, loop back if loops or end everything
            elif binary_data[cursor:cursor+8] == "00111011":
                if loop_times > 0:
                    loop_times -= 1
                    if loop_times == 0:
                        end_of_file = True
                    cursor = 0
                elif loop_times == 0:
                    cursor = 0
                elif loop_times == -1:
                    end_of_file = True
                continue
            
            # if graphics control extension
            elif binary_data[cursor:cursor+16] == "0010000111111001":
                cursor += 24
                packet_field = binary_data[cursor:cursor+8]
                time_delay = binary_data[cursor+8:cursor+24]
                transparent_colour_index = binary_data[cursor+24:cursor+32]
                cursor += 40

                disposal = binary_to_decimal(packet_field[3:6])
                transparency_flag = binary_to_decimal(packet_field[7])
                time_delay = little_binary_to_decimal(time_delay)
                transparent_colour_index = binary_to_decimal(transparent_colour_index)
                # print(disposal, transparency_flag, time_delay, transparent_colour_index)

            
            # if imagee descriptorrr!!
            elif binary_data[cursor:cursor+8] == "00101100":
                cursor += 8
                image_left = binary_data[cursor:cursor+16]
                image_top = binary_data[cursor+16:cursor+32]
                image_width = binary_data[cursor+32:cursor+48]
                image_height = binary_data[cursor+48:cursor+64]
                packet_field = binary_data[cursor+64:cursor+72]
                cursor += 72

                image_left = little_binary_to_decimal(image_left)
                image_top = little_binary_to_decimal(image_top)
                image_width = little_binary_to_decimal(image_width)
                image_height = little_binary_to_decimal(image_height)
                # print(image_left, image_top, image_width, image_height)

                local_colour_table = packet_field[0]
                interlace_flag = packet_field[1]
                sort_flag = packet_field[2]
                num_local_colours = packet_field[5:8]

                local_colour_table = binary_to_decimal(local_colour_table)
                interlace_flag = binary_to_decimal(interlace_flag)
                sort_flag = binary_to_decimal(sort_flag)
                num_local_colours = 2 ** (binary_to_decimal(num_local_colours) + 1)
                # print(local_colour_table, interlace_flag, sort_flag, num_local_colours)
                
                if local_colour_table:
                    local_colours = []
                    for i in range(0, num_local_colours*3*8, 3*8):
                        r = binary_to_decimal(binary_data[cursor+i: cursor+i+8])
                        g = binary_to_decimal(binary_data[cursor+i+8: cursor+i+8*2])
                        b = binary_to_decimal(binary_data[cursor+i+8*2: cursor+i+8*3])
                        local_colours.append(
                            (r, g, b)
                        )
                    cursor += num_local_colours*3*8

                lzw_minimum_code_size = binary_data[cursor:cursor+8]
                lzw_minimum_code_size = binary_to_decimal(lzw_minimum_code_size)
                cursor += 8

                current_code_size = lzw_minimum_code_size + 1
                codes = [c for c in range(2**lzw_minimum_code_size+2)]
                code_values = [[c] for c in range(2**lzw_minimum_code_size)] + ["cc"] + ["eoi"]
                index_stream = []

                image_bytes = ""

                # scroll through the image data and reverse every byte
                while binary_data[cursor:cursor+8] != "00000000":
                    length = binary_to_decimal(binary_data[cursor:cursor+8])
                    cursor += 8
                    

                    cursor_at_end = cursor + length*8
                    for i in range(cursor, cursor_at_end, 8):
                        image_bytes += binary_data[i:i+8][::-1]
                    cursor = cursor_at_end
                cursor += 8

                # other code to parse with the better byte stream
                code = image_bytes[:current_code_size][::-1]
                code = binary_to_decimal(code)
                image_bytes = image_bytes[current_code_size:]
                
                if code_values[code] == "cc":
                    current_code_size = lzw_minimum_code_size + 1
                    codes = [c for c in range(2**lzw_minimum_code_size+2)]
                    code_values = [[c] for c in range(2**lzw_minimum_code_size)] + ["cc"] + ["eoi"]
                    
                    code = image_bytes[:current_code_size][::-1]
                    code = binary_to_decimal(code)
                    image_bytes = image_bytes[current_code_size:]

                index_stream.append(code)
                prev_code = code

                while len(image_bytes) > 0:
                    code = image_bytes[:current_code_size][::-1]
                    # print(code)
                    code = binary_to_decimal(code)
                    image_bytes = image_bytes[current_code_size:]

                    if code in codes:
                        if code_values[code] == "cc":
                            current_code_size = lzw_minimum_code_size + 1
                            codes = [c for c in range(2**lzw_minimum_code_size+2)]
                            code_values = [[c] for c in range(2**lzw_minimum_code_size)] + ["cc"] + ["eoi"]
                            
                            code = image_bytes[:current_code_size][::-1]
                            code = binary_to_decimal(code)
                            image_bytes = image_bytes[current_code_size:]
                        elif code_values[code] == "eoi":
                            break
                        code_value = code_values[codes.index(code)]
                        index_stream.extend(code_value)
                        k = code_value[0]
                        prev_code_value = code_values[codes.index(prev_code)]
                        codes.append(codes[-1]+1)
                        code_values.append([c for c in prev_code_value]+[k])
                        prev_code = code
                    else:
                        prev_code_value = code_values[codes.index(prev_code)]
                        k = prev_code_value[0]
                        index_stream.extend([c for c in prev_code_value]+[k])
                        codes.append(codes[-1]+1)
                        code_values.append([c for c in prev_code_value]+[k])
                        prev_code = code
                    
                    if codes[-1] == 2**(current_code_size)-1:
                        current_code_size += 1

                # print(index_stream)
                
                # draw the index_stream based on whatever data you have.
                if background_colour_index == "1":
                    background_colour = global_colours[background_colour_index]
                if disposal == 2:
                    img = Image.new("RGB", (width, height), background_colour)

                for i in range(len(index_stream)):
                    x = i % image_width + image_left
                    y = i // image_width + image_top
                    if local_colour_table:
                        colour = local_colours[index_stream[i]]
                    else:
                        colour = global_colours[index_stream[i]]
                    if transparency_flag:
                        if index_stream[i] == transparent_colour_index:
                            continue
                    img.putpixel((x, y), colour)
                img.save(f"frames/{cursor}.png", "PNG")

                continue
            
        else:
            cursor += 8