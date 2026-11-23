// AEEHelperFuncs oficial — gerado de AEEStdLib.h (BREW 4.0.2 SP19 SDK) pelo
// guard do Curupira (tools/verificar_ajudantes.sh), conferido com ancoras.
constexpr unsigned kAjudante_memmove = 0x000;
constexpr unsigned kAjudante_memset = 0x004;
constexpr unsigned kAjudante_strcpy = 0x008;
constexpr unsigned kAjudante_strcat = 0x00C;
constexpr unsigned kAjudante_strcmp = 0x010;
constexpr unsigned kAjudante_strlen = 0x014;
constexpr unsigned kAjudante_strchr = 0x018;
constexpr unsigned kAjudante_strrchr = 0x01C;
constexpr unsigned kAjudante_sprintf = 0x020;
constexpr unsigned kAjudante_wstrcpy = 0x024;
constexpr unsigned kAjudante_wstrcat = 0x028;
constexpr unsigned kAjudante_wstrcmp = 0x02C;
constexpr unsigned kAjudante_wstrlen = 0x030;
constexpr unsigned kAjudante_wstrchr = 0x034;
constexpr unsigned kAjudante_wstrrchr = 0x038;
constexpr unsigned kAjudante_wsprintf = 0x03C;
constexpr unsigned kAjudante_strtowstr = 0x040;
constexpr unsigned kAjudante_wstrtostr = 0x044;
constexpr unsigned kAjudante_wstrtofloat = 0x048;
constexpr unsigned kAjudante_floattowstr = 0x04C;
constexpr unsigned kAjudante_utf8towstr = 0x050;
constexpr unsigned kAjudante_wstrtoutf8 = 0x054;
constexpr unsigned kAjudante_wstrlower = 0x058;
constexpr unsigned kAjudante_wstrupper = 0x05C;
constexpr unsigned kAjudante_chartype = 0x060;
constexpr unsigned kAjudante_SetupNativeImage = 0x064;
constexpr unsigned kAjudante_malloc = 0x068;
constexpr unsigned kAjudante_free = 0x06C;
constexpr unsigned kAjudante_wstrdup = 0x070;
constexpr unsigned kAjudante_realloc = 0x074;
constexpr unsigned kAjudante_wwritelongex = 0x078;
constexpr unsigned kAjudante_wstrsize = 0x07C;
constexpr unsigned kAjudante_wstrncopyn = 0x080;
constexpr unsigned kAjudante_OEMStrLen = 0x084;
constexpr unsigned kAjudante_OEMStrSize = 0x088;
constexpr unsigned kAjudante_GetAEEVersion = 0x08C;
constexpr unsigned kAjudante_atoi = 0x090;
constexpr unsigned kAjudante_f_op = 0x094;
constexpr unsigned kAjudante_f_cmp = 0x098;
constexpr unsigned kAjudante_dbgprintf = 0x09C;
constexpr unsigned kAjudante_wstrcompress = 0x0A0;
constexpr unsigned kAjudante_aee_LocalTimeOffset = 0x0A4;
constexpr unsigned kAjudante_aee_GetRand = 0x0A8;
constexpr unsigned kAjudante_aee_GetTimeMS = 0x0AC;
constexpr unsigned kAjudante_aee_GetUpTimeMS = 0x0B0;
constexpr unsigned kAjudante_aee_GetSeconds = 0x0B4;
constexpr unsigned kAjudante_aee_GetJulianDate = 0x0B8;
constexpr unsigned kAjudante_sysfree = 0x0BC;
constexpr unsigned kAjudante_GetAppInstance = 0x0C0;
constexpr unsigned kAjudante_strtoul = 0x0C4;
constexpr unsigned kAjudante_strncpy = 0x0C8;
constexpr unsigned kAjudante_strncmp = 0x0CC;
constexpr unsigned kAjudante_stricmp = 0x0D0;
constexpr unsigned kAjudante_strnicmp = 0x0D4;
constexpr unsigned kAjudante_strstr = 0x0D8;
constexpr unsigned kAjudante_memcmp = 0x0DC;
constexpr unsigned kAjudante_memchr = 0x0E0;
constexpr unsigned kAjudante_strexpand = 0x0E4;
constexpr unsigned kAjudante_stristr = 0x0E8;
constexpr unsigned kAjudante_memstr = 0x0EC;
constexpr unsigned kAjudante_wstrncmp = 0x0F0;
constexpr unsigned kAjudante_strdup = 0x0F4;
constexpr unsigned kAjudante_strbegins = 0x0F8;
constexpr unsigned kAjudante_strends = 0x0FC;
constexpr unsigned kAjudante_strchrend = 0x100;
constexpr unsigned kAjudante_strchrsend = 0x104;
constexpr unsigned kAjudante_memrchr = 0x108;
constexpr unsigned kAjudante_memchrend = 0x10C;
constexpr unsigned kAjudante_memrchrbegin = 0x110;
constexpr unsigned kAjudante_strlower = 0x114;
constexpr unsigned kAjudante_strupper = 0x118;
constexpr unsigned kAjudante_wstricmp = 0x11C;
constexpr unsigned kAjudante_wstrnicmp = 0x120;
constexpr unsigned kAjudante_inet_aton = 0x124;
constexpr unsigned kAjudante_inet_ntoa = 0x128;
constexpr unsigned kAjudante_swapl = 0x12C;
constexpr unsigned kAjudante_swaps = 0x130;
constexpr unsigned kAjudante_GetFSFree = 0x134;
constexpr unsigned kAjudante_GetRAMFree = 0x138;
constexpr unsigned kAjudante_vsprintf = 0x13C;
constexpr unsigned kAjudante_vsnprintf = 0x140;
constexpr unsigned kAjudante_snprintf = 0x144;
constexpr unsigned kAjudante_aee_JulianToSeconds = 0x148;
constexpr unsigned kAjudante_strlcpy = 0x14C;
constexpr unsigned kAjudante_strlcat = 0x150;
constexpr unsigned kAjudante_wstrlcpy = 0x154;
constexpr unsigned kAjudante_wstrlcat = 0x158;
constexpr unsigned kAjudante_setstaticptr = 0x15C;
constexpr unsigned kAjudante_f_assignstr = 0x160;
constexpr unsigned kAjudante_f_assignint = 0x164;
constexpr unsigned kAjudante_wwritelong = 0x168;
constexpr unsigned kAjudante_dbgheapmark = 0x16C;
constexpr unsigned kAjudante_lockmem = 0x170;
constexpr unsigned kAjudante_unlockmem = 0x174;
constexpr unsigned kAjudante_dumpheap = 0x178;
constexpr unsigned kAjudante_strtod = 0x17C;
constexpr unsigned kAjudante_f_calc = 0x180;
constexpr unsigned kAjudante_sleep = 0x184;
constexpr unsigned kAjudante_getlasterror = 0x188;
constexpr unsigned kAjudante_wgs84_to_degrees = 0x18C;
constexpr unsigned kAjudante_dbgevent = 0x190;
constexpr unsigned kAjudante_aee_IsBadPtr = 0x194;
constexpr unsigned kAjudante_aee_basename = 0x198;
constexpr unsigned kAjudante_aee_makepath = 0x19C;
constexpr unsigned kAjudante_aee_splitpath = 0x1A0;
constexpr unsigned kAjudante_aee_stribegins = 0x1A4;
constexpr unsigned kAjudante_aee_GetUTCSeconds = 0x1A8;
constexpr unsigned kAjudante_f_toint = 0x1AC;
constexpr unsigned kAjudante_f_get = 0x1B0;
constexpr unsigned kAjudante_qsort = 0x1B4;
constexpr unsigned kAjudante_trunc = 0x1B8;
constexpr unsigned kAjudante_utrunc = 0x1BC;
constexpr unsigned kAjudante_err_realloc = 0x1C0;
constexpr unsigned kAjudante_err_strdup = 0x1C4;
constexpr unsigned kAjudante_inet_pton = 0x1C8;
constexpr unsigned kAjudante_inet_ntop = 0x1CC;
constexpr unsigned kAjudante_GetALSContext = 0x1D0;

// pares: {offset, nome}
{0x000, "memmove"},
{0x004, "memset"},
{0x008, "strcpy"},
{0x00C, "strcat"},
{0x010, "strcmp"},
{0x014, "strlen"},
{0x018, "strchr"},
{0x01C, "strrchr"},
{0x020, "sprintf"},
{0x024, "wstrcpy"},
{0x028, "wstrcat"},
{0x02C, "wstrcmp"},
{0x030, "wstrlen"},
{0x034, "wstrchr"},
{0x038, "wstrrchr"},
{0x03C, "wsprintf"},
{0x040, "strtowstr"},
{0x044, "wstrtostr"},
{0x048, "wstrtofloat"},
{0x04C, "floattowstr"},
{0x050, "utf8towstr"},
{0x054, "wstrtoutf8"},
{0x058, "wstrlower"},
{0x05C, "wstrupper"},
{0x060, "chartype"},
{0x064, "SetupNativeImage"},
{0x068, "malloc"},
{0x06C, "free"},
{0x070, "wstrdup"},
{0x074, "realloc"},
{0x078, "wwritelongex"},
{0x07C, "wstrsize"},
{0x080, "wstrncopyn"},
{0x084, "OEMStrLen"},
{0x088, "OEMStrSize"},
{0x08C, "GetAEEVersion"},
{0x090, "atoi"},
{0x094, "f_op"},
{0x098, "f_cmp"},
{0x09C, "dbgprintf"},
{0x0A0, "wstrcompress"},
{0x0A4, "aee_LocalTimeOffset"},
{0x0A8, "aee_GetRand"},
{0x0AC, "aee_GetTimeMS"},
{0x0B0, "aee_GetUpTimeMS"},
{0x0B4, "aee_GetSeconds"},
{0x0B8, "aee_GetJulianDate"},
{0x0BC, "sysfree"},
{0x0C0, "GetAppInstance"},
{0x0C4, "strtoul"},
{0x0C8, "strncpy"},
{0x0CC, "strncmp"},
{0x0D0, "stricmp"},
{0x0D4, "strnicmp"},
{0x0D8, "strstr"},
{0x0DC, "memcmp"},
{0x0E0, "memchr"},
{0x0E4, "strexpand"},
{0x0E8, "stristr"},
{0x0EC, "memstr"},
{0x0F0, "wstrncmp"},
{0x0F4, "strdup"},
{0x0F8, "strbegins"},
{0x0FC, "strends"},
{0x100, "strchrend"},
{0x104, "strchrsend"},
{0x108, "memrchr"},
{0x10C, "memchrend"},
{0x110, "memrchrbegin"},
{0x114, "strlower"},
{0x118, "strupper"},
{0x11C, "wstricmp"},
{0x120, "wstrnicmp"},
{0x124, "inet_aton"},
{0x128, "inet_ntoa"},
{0x12C, "swapl"},
{0x130, "swaps"},
{0x134, "GetFSFree"},
{0x138, "GetRAMFree"},
{0x13C, "vsprintf"},
{0x140, "vsnprintf"},
{0x144, "snprintf"},
{0x148, "aee_JulianToSeconds"},
{0x14C, "strlcpy"},
{0x150, "strlcat"},
{0x154, "wstrlcpy"},
{0x158, "wstrlcat"},
{0x15C, "setstaticptr"},
{0x160, "f_assignstr"},
{0x164, "f_assignint"},
{0x168, "wwritelong"},
{0x16C, "dbgheapmark"},
{0x170, "lockmem"},
{0x174, "unlockmem"},
{0x178, "dumpheap"},
{0x17C, "strtod"},
{0x180, "f_calc"},
{0x184, "sleep"},
{0x188, "getlasterror"},
{0x18C, "wgs84_to_degrees"},
{0x190, "dbgevent"},
{0x194, "aee_IsBadPtr"},
{0x198, "aee_basename"},
{0x19C, "aee_makepath"},
{0x1A0, "aee_splitpath"},
{0x1A4, "aee_stribegins"},
{0x1A8, "aee_GetUTCSeconds"},
{0x1AC, "f_toint"},
{0x1B0, "f_get"},
{0x1B4, "qsort"},
{0x1B8, "trunc"},
{0x1BC, "utrunc"},
{0x1C0, "err_realloc"},
{0x1C4, "err_strdup"},
{0x1C8, "inet_pton"},
{0x1CC, "inet_ntop"},
{0x1D0, "GetALSContext"},
