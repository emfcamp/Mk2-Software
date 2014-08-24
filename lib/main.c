#include <iostream>
#include "uECC.h"
#include <string>
#include <stdlib.h>

int char2int(uint8_t input)
{
    if(input >= '0' && input <= '9')
        return input - '0';
    if(input >= 'A' && input <= 'F')
        return input - 'A' + 10;
    if(input >= 'a' && input <= 'f')
        return input - 'a' + 10;
    throw "Invalid input string";
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        std::cerr << "Define mode: sign | verify | create";
        return 1;
    }

    std::string mode(argv[1]);

    // secp160r1
    //
    uint8_t l_private[uECC_BYTES];
    uint8_t l_public[uECC_BYTES * 2];

    if (mode.compare("create") == 0) {
        uECC_make_key(l_public, l_private);

        std::cout << "PUBLIC:\n";
        for (int i=0; i<uECC_BYTES*2; i++) {
            std::cout << "0123456789abcdef"[l_public[i]>>4];
            std::cout << "0123456789abcdef"[l_public[i]&0xf];
        }
        std::cout << "\n\nPRIVATE:\n";
        for (int i=0; i<uECC_BYTES; i++) {
            std::cout << "0123456789abcdef"[l_private[i]>>4];
            std::cout << "0123456789abcdef"[l_private[i]&0xf];
        }
        std::cout << "\n";

        return 0;
    }



    if (mode.compare("sign") == 0) {
        std::string privateKeyAsHex(getenv("EMF_PRIVATE_KEY"));
        for (int i=0; i<uECC_BYTES; i++) {
            l_private[i] = char2int(privateKeyAsHex[i * 2]) * 16 + char2int(privateKeyAsHex[i * 2 + 1]);
        }

        uint8_t l_hash[uECC_BYTES];
        uint8_t l_sig[uECC_BYTES*2];

        for (int i=0; i<20; i++) {
            char e1, e2;
            std::cin >> e1;
            std::cin >> e2;
            l_hash[i] = char2int(e1) * 16 + char2int(e2);
        }

        if(uECC_sign(l_private, l_hash, l_sig)) {
            //if (uECC_verify(l_public, l_hash, l_sig)) {
                for (int i=0; i<uECC_BYTES; i++) {
                    std::cout << "0123456789abcdef"[l_hash[i]>>4];
                    std::cout << "0123456789abcdef"[l_hash[i]&0xf];
                }
                std::cout << "\n";
                for (int i=0; i<uECC_BYTES*2; i++) {
                    std::cout << "0123456789abcdef"[l_sig[i]>>4];
                    std::cout << "0123456789abcdef"[l_sig[i]&0xf];
                }

                return 0;
            //} else {
            //    std::cerr << "Could not verify created signature";
            //    return 1;
            //}
        } else {
            std::cerr << "Could not create signature";
            return 1;
        }


    }

    if (mode.compare("verify") == 0) {
        std::string publicKeyInHex(getenv("EMF_PUBLIC_KEY"));
        for (int i=0; i<uECC_BYTES * 2; i++) {
            l_public[i] = char2int(publicKeyInHex[i * 2]) * 16 + char2int(publicKeyInHex[i * 2 + 1]);
        }

        uint8_t l_hash[uECC_BYTES];
        uint8_t l_sig[uECC_BYTES*2];

        for (int i=0; i<uECC_BYTES; i++) {
            char e1 = ' ';
            while (!((e1 >= '0' && e1 <= '9') || (e1 >= 'a' && e1 <= 'f') || (e1 >= 'A' && e1 <= 'F'))) {
                std::cin >> e1;
            }
            char e2;
            std::cin >> e2;
            l_hash[i] = char2int(e1) * 16 + char2int(e2);
        }

        for (int i=0; i<uECC_BYTES * 2; i++) {
            char e1 = ' ';
            while (!((e1 >= '0' && e1 <= '9') || (e1 >= 'a' && e1 <= 'f') || (e1 >= 'A' && e1 <= 'F'))) {
                std::cin >> e1;
            }
            char e2;
            std::cin >> e2;
            l_sig[i] = char2int(e1) * 16 + char2int(e2);
        }

        if(uECC_verify(l_public, l_hash, l_sig)) {
            std::cout << "OK\n";
            return 0;
        } else {
            std::cout << "Invalid\n";
            return 1;
        }
    }

    std::cerr << "Onvalid mode: sign | verify";
    return 1;
}