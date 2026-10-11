#include "libretro.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static const char *region, *prefix, *hardware;
static unsigned pixel_format, captured, run_frame;
static bool env(unsigned cmd, void *data) {
  switch(cmd) {
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
      *(const char **)data = "/private/tmp/198x-sms-raster-evidence/empty"; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
      struct retro_variable *v=data; v->value=NULL;
      if (!strcmp(v->key,"genesis_plus_gx_region_detect")) v->value=region;
      if (!strcmp(v->key,"genesis_plus_gx_system_hw")) v->value=hardware;
      return v->value!=NULL;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data=false; return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION: *(unsigned *)data=0; return true;
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: pixel_format=*(unsigned *)data; return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data=true; return true;
    default: return false;
  }
}
static uint8_t *pixels; static unsigned width,height;
static void video(const void *data,unsigned w,unsigned h,size_t pitch) {
  if(!data || data==RETRO_HW_FRAME_BUFFER_VALID) return;
  free(pixels); pixels=malloc(w*h*3); if(!pixels) abort(); width=w; height=h; captured++;
  for(unsigned y=0;y<h;y++) for(unsigned x=0;x<w;x++) {
    unsigned r,g,b;
    if(pixel_format==RETRO_PIXEL_FORMAT_XRGB8888) {
      uint32_t p=((const uint32_t *)((const uint8_t *)data+y*pitch))[x]; r=(p>>16)&255; g=(p>>8)&255; b=p&255;
    } else {
      uint16_t p=((const uint16_t *)((const uint8_t *)data+y*pitch))[x];
      if(pixel_format==RETRO_PIXEL_FORMAT_RGB565) {r=((p>>11)&31)*255/31; g=((p>>5)&63)*255/63;}
      else {r=((p>>10)&31)*255/31; g=((p>>5)&31)*255/31;}
      b=(p&31)*255/31;
    }
    size_t i=(y*w+x)*3; pixels[i]=r; pixels[i+1]=g; pixels[i+2]=b;
  }
}
static void audio(int16_t l,int16_t r) {(void)l;(void)r;}
static size_t batch(const int16_t *data,size_t n) {(void)data;return n;}
static void poll(void) {}
static int16_t input(unsigned p,unsigned d,unsigned i,unsigned id) {
 (void)i; return p==0 && d==RETRO_DEVICE_JOYPAD && id==RETRO_DEVICE_ID_JOYPAD_B && ((run_frame>=200 && run_frame<205) || (run_frame>=400 && run_frame<405) || (run_frame>=1000 && run_frame<1005));
}
int main(int argc,char **argv) {
  if(argc!=5) return 2; region=argv[2]; prefix=argv[3]; hardware=strstr(argv[1],".gg") ? "game gear" : "master system II"; int frames=atoi(argv[4]); if(frames<1) return 2;
  FILE *f=fopen(argv[1],"rb"); if(!f) return 3; fseek(f,0,SEEK_END); long len=ftell(f); rewind(f);
  uint8_t *rom=malloc(len); if(!rom || fread(rom,1,len,f)!=(size_t)len) return 4; fclose(f);
  retro_set_environment(env); retro_set_video_refresh(video); retro_set_audio_sample(audio); retro_set_audio_sample_batch(batch); retro_set_input_poll(poll); retro_set_input_state(input); retro_init();
  struct retro_game_info game={argv[1],rom,(size_t)len,NULL}; if(!retro_load_game(&game)) return 5;
  for(run_frame=0;run_frame<(unsigned)frames;run_frame++) retro_run();
  if(!captured || !pixels) return 6;
  char path[1024]; snprintf(path,sizeof(path),"%s.ppm",prefix); f=fopen(path,"wb"); if(!f) return 7;
  fprintf(f,"P6\n%u %u\n255\n",width,height); fwrite(pixels,3,width*height,f); fclose(f);
  size_t n=retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM); void *ram=retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM); if(!ram || n<8192) return 8;
  snprintf(path,sizeof(path),"%s.ram",prefix); f=fopen(path,"wb"); if(!f) return 9; fwrite(ram,1,n,f); fclose(f);
  printf("region=%s frames=%d captures=%u pixels=%ux%u format=%u ram=%zu\n",region,frames,captured,width,height,pixel_format,n);
  retro_unload_game(); retro_deinit(); free(rom); free(pixels); return 0;
}
