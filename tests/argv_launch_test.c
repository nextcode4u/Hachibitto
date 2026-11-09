/* SPDX-License-Identifier: MIT */
#include "emulator_stubs.h"
#include "argv_launch.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
struct Media MyMedia[3];
int bMainMenuActive;
static int loaded, music, slot, fail_load;
static char received[132];
void UpperScreenMainMenu(void) {}
void BottomScreenMainMenu(void) {}
void DisplayFileNames(void) {}
void CheckIfGameHasMusicMapper(void) { ++music; }
void LoadGameIntoMedia(int media, char *name) {
    ++loaded; slot = media; strcpy(received, name);
    MyMedia[media].filesize = fail_load ? 0 : 64;
}
int main(void) {
    char root[] = "/tmp/hachibitto-argv-XXXXXX", previous[1024];
    assert(getcwd(previous, sizeof(previous)) && mkdtemp(root));
    const char *names[] = {"Game With Spaces.MX2", "Disk.MXD", "Native.rom", "Native.bin", "Native.dsk"};
    for (unsigned i = 0; i < sizeof(names)/sizeof(names[0]); ++i) {
        assert(chdir(root) == 0);
        FILE *file = fopen(names[i], "wb"); assert(file); fputs("Synthetic fixture", file); fclose(file);
        char app[] = "Hachibitto.nds", argument[132]; strcpy(argument, names[i]);
        char *args[] = {app, argument};
        assert(argv_launch_prepare(2, args));
        assert(chdir("/") == 0); // Default browser directory must not alter the request.
        assert(argv_launch_start());
        assert(slot == ((i == 1 || i == 4) ? MEDIA_DISK : MEDIA_CART1));
        assert(!strcmp(received, names[i]) && !strcmp(argument, names[i]));
        assert(!bMainMenuActive && !argv_launch_start());
        assert(chdir(root) == 0); unlink(names[i]);
    }
    assert(loaded == 5 && music == 5);
    assert(!argv_launch_prepare(0, NULL));
    char app[] = "app.nds", missing[] = "missing.mx2"; char *args[] = {app, missing};
    assert(!argv_launch_prepare(2, args));
    FILE *file = fopen("Broken.mx2", "wb"); assert(file); fputs("Synthetic fixture", file); fclose(file);
    args[1] = "Broken.mx2"; assert(argv_launch_prepare(2, args));
    fail_load = 1; assert(chdir("/") == 0); assert(!argv_launch_start());
    char cwd[256]; assert(getcwd(cwd, sizeof(cwd)) && !strcmp(cwd, "/"));
    assert(!bMainMenuActive && !argv_launch_start());
    assert(chdir(root) == 0); unlink("Broken.mx2");
    assert(chdir(previous) == 0); rmdir(root);
}
