/* SPDX-License-Identifier: MIT
 * Launch once through the same media/configuration path as the browser.
 */
#include "argv_launch.h"
#include "argv_path.h"
#include "Hachibitto.h"
#include "MSX_generic.h"
#include <unistd.h>

static char launch_directory[MAX_PATH_NAME_LEN];
static char launch_filename[MAX_FILE_NAME_LEN];
static int launch_media;
static int launch_pending;
extern void CheckIfGameHasMusicMapper(void);

int argv_launch_prepare(int argc, char **argv)
{
    char base[MAX_PATH_NAME_LEN];
    launch_pending = 0;
    if (argc < 2 || !argv || !argv[1] || !argv_path_select_root(argv[1])
        || !getcwd(base, sizeof(base)))
        return 0;
    if (!argv_path_prepare(argv[1], base, launch_directory, sizeof(launch_directory),
                              launch_filename, sizeof(launch_filename)))
        return 0;
    if (argv_path_extension(launch_filename, ".dsk") || argv_path_extension(launch_filename, ".mxd"))
        launch_media = MEDIA_DISK;
    else if (argv_path_extension(launch_filename, ".rom") || argv_path_extension(launch_filename, ".bin")
             || argv_path_extension(launch_filename, ".mx2"))
        launch_media = MEDIA_CART1;
    else
        return 0;
    launch_pending = 1;
    return 1;
}

int argv_launch_start(void)
{
    char previous[MAX_PATH_NAME_LEN], canonical[MAX_PATH_NAME_LEN];
    if (!launch_pending)
        return 0;
    launch_pending = 0;
    if (!getcwd(previous, sizeof(previous)) || chdir(launch_directory) != 0)
        return 0;
    if (!getcwd(canonical, sizeof(canonical)))
    {
        chdir(previous);
        return 0;
    }
    bMainMenuActive = 1;
    UpperScreenMainMenu();
    BottomScreenMainMenu();
    LoadGameIntoMedia(launch_media, launch_filename);
    if (!MyMedia[launch_media].filesize)
    {
        bMainMenuActive = 0;
        chdir(previous);
        return 0;
    }
    CheckIfGameHasMusicMapper();
    BottomScreenMainMenu();
    DisplayFileNames();
    bMainMenuActive = 0;
    return 1;
}
