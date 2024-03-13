#version 330 core

uniform bool awake;
uniform float t;
uniform float vertRat;
uniform vec2 screenSize;
uniform sampler2D tex;
uniform sampler2D field;
uniform sampler2D stars1;
uniform sampler2D stars2;
uniform sampler2D noise;

in vec2 uvs;
out vec4 f_color;

const vec2 texelSize = 1.0 / vec2(320, 320);

void main() {
    float off = texture(noise, vec2(uvs.x + t*0.01, uvs.y*3 + t*0.005))[0]/500;
    vec2 base_pos = uvs;
    if (!awake) {
        base_pos = vec2(
            min(float(screenSize[0] - 1)/screenSize[0], uvs.x + off),
            min(float(screenSize[1] - 1)/screenSize[1], uvs.y + off)
        );
    }
    f_color = texture(tex, base_pos);
    if (f_color == vec4(1.0, 0, 0, 0)) {
        vec2 pos = vec2(base_pos.x * 20 - t*0.7, base_pos.y * 20 + t*0.3 + 0.1*sin(15*base_pos.y + 5*base_pos.x + t));
        f_color = texture(field, pos).bgra;
    }
    if (f_color == vec4(0, 0, 0, 0)) {
        vec2 pos1 = vec2(base_pos.x/1.5 + t/650, base_pos.y/1.5 * vertRat - t/400);
        f_color = texture(stars1, pos1 + vec2(-1, 2) * texelSize) * 2.0;
        f_color += texture(stars1, pos1 + vec2(0, 2) * texelSize) * 8.0;
        f_color += texture(stars1, pos1 + vec2(1, 2) * texelSize) * 2.0;

        f_color += texture(stars1, pos1 + vec2(-2, 1) * texelSize) * 2.0;
        f_color += texture(stars1, pos1 + vec2(-1, 1) * texelSize) * 6.0;
        f_color += texture(stars1, pos1 + vec2(0, 1) * texelSize) * 24.0;
        f_color += texture(stars1, pos1 + vec2(1, 1) * texelSize) * 6.0;
        f_color += texture(stars1, pos1 + vec2(2, 1) * texelSize) * 2.0;

        f_color += texture(stars1, pos1 + vec2(-2, 0) * texelSize) * 8.0;
        f_color += texture(stars1, pos1 + vec2(-1, 0) * texelSize) * 24.0;
        f_color += texture(stars1, pos1) * 36.0;
        f_color += texture(stars1, pos1 + vec2(1, 0) * texelSize) * 24.0;
        f_color += texture(stars1, pos1 + vec2(2, 0) * texelSize) * 8.0;

        f_color += texture(stars1, pos1 + vec2(-2, -1) * texelSize) * 2.0;
        f_color += texture(stars1, pos1 + vec2(-1, -1) * texelSize) * 6.0;
        f_color += texture(stars1, pos1 + vec2(0, -1) * texelSize) * 24.0;
        f_color += texture(stars1, pos1 + vec2(1, -1) * texelSize) * 6.0;
        f_color += texture(stars1, pos1 + vec2(2, -1) * texelSize) * 2.0;

        f_color += texture(stars1, pos1 + vec2(-1, -2) * texelSize) * 2.0;
        f_color += texture(stars1, pos1 + vec2(0, -2) * texelSize) * 8.0;
        f_color += texture(stars1, pos1 + vec2(1, -2) * texelSize) * 2.0;
        
        vec2 pos2 = vec2(base_pos.x/1.2 + t/300, base_pos.y/1.2 * vertRat + t/500);
        f_color += texture(stars2, pos2 + vec2(-1, 2) * texelSize) * 2.0;
        f_color += texture(stars2, pos2 + vec2(0, 2) * texelSize) * 8.0;
        f_color += texture(stars2, pos2 + vec2(1, 2) * texelSize) * 2.0;

        f_color += texture(stars2, pos2 + vec2(-2, 1) * texelSize) * 2.0;
        f_color += texture(stars2, pos2 + vec2(-1, 1) * texelSize) * 6.0;
        f_color += texture(stars2, pos2 + vec2(0, 1) * texelSize) * 24.0;
        f_color += texture(stars2, pos2 + vec2(1, 1) * texelSize) * 6.0;
        f_color += texture(stars2, pos2 + vec2(2, 1) * texelSize) * 2.0;

        f_color += texture(stars2, pos2 + vec2(-2, 0) * texelSize) * 8.0;
        f_color += texture(stars2, pos2 + vec2(-1, 0) * texelSize) * 24.0;
        f_color += texture(stars2, pos2) * 36.0;
        f_color += texture(stars2, pos2 + vec2(1, 0) * texelSize) * 24.0;
        f_color += texture(stars2, pos2 + vec2(2, 0) * texelSize) * 8.0;

        f_color += texture(stars2, pos2 + vec2(-2, -1) * texelSize) * 2.0;
        f_color += texture(stars2, pos2 + vec2(-1, -1) * texelSize) * 6.0;
        f_color += texture(stars2, pos2 + vec2(0, -1) * texelSize) * 24.0;
        f_color += texture(stars2, pos2 + vec2(1, -1) * texelSize) * 6.0;
        f_color += texture(stars2, pos2 + vec2(2, -1) * texelSize) * 2.0;

        f_color += texture(stars2, pos2 + vec2(-1, -2) * texelSize) * 2.0;
        f_color += texture(stars2, pos2 + vec2(0, -2) * texelSize) * 8.0;
        f_color += texture(stars2, pos2 + vec2(1, -2) * texelSize) * 2.0;

        f_color /= 64;
        f_color = vec4(min(1, f_color.r), min(1, f_color.g), min(1, f_color.b), 1);
    }
}
