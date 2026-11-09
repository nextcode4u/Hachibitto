#ifndef EMULATOR_STUBS_H
#define EMULATOR_STUBS_H
#define MAX_PATH_NAME_LEN 200
#define MAX_FILE_NAME_LEN 132
#define MEDIA_CART1 0
#define MEDIA_DISK 2
struct Media { unsigned filesize; };
extern struct Media MyMedia[3];
extern int bMainMenuActive;
void UpperScreenMainMenu(void);
void BottomScreenMainMenu(void);
void LoadGameIntoMedia(int, char *);
void DisplayFileNames(void);
#endif
