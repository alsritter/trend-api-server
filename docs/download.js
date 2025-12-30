const https = require('https');
const fs = require('fs');
const path = require('path');

function downloadImage(url, filepath) {
    const file = fs.createWriteStream(filepath);
    
    https.get(url, (response) => {
        response.pipe(file);
        
        file.on('finish', () => {
            file.close();
            console.log('下载完成:', filepath);
        });
    }).on('error', (err) => {
        fs.unlink(filepath, () => {});
        console.error('下载失败:', err.message);
    });
}

// 使用示例
const imageUrl = 'https://p26-sign.douyinpic.com/tos-cn-p-0015/oUeR7kwuSQGfBcBTJCoLbZjIQ7GHvdAIFAeUGi~noop.jpeg?lk3s=bfd515bb&x-expires=1766995200&x-signature=yWHAHBybIbScyw1rLDePwce37VI%3D&from=3218412987';
const savePath = './douyin_image.jpg';

downloadImage(imageUrl, savePath);