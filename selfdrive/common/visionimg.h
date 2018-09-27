#ifndef VISIONIMG_H
#define VISIONIMG_H

#ifdef QCOM
#include <GLES3/gl3.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#endif

#include "common/visionbuf.h"

#ifdef __cplusplus
extern "C" {
#endif

#define VISIONIMG_FORMAT_RGB24 1

typedef struct VisionImg {
  int fd;
  int format;
  int width, height, stride;
  int bpp;
  size_t size;
} VisionImg;

<<<<<<< HEAD
=======
void visionimg_compute_aligned_width_and_height(int width, int height, int *aligned_w, int *aligned_h);
>>>>>>> a422246dc30bce11e970514f13f7c110f4470cc3
VisionImg visionimg_alloc_rgb24(int width, int height, VisionBuf *out_buf);

#ifdef QCOM
EGLClientBuffer visionimg_to_egl(const VisionImg *img);
GLuint visionimg_to_gl(const VisionImg *img);
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif
