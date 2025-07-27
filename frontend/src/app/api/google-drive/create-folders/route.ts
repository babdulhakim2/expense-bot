import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";
import { BusinessService } from "@/lib/firebase/services/business-service";

export async function POST(request: NextRequest) {
  try {
    const session = (await getServerSession(authOptions)) as any;
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { businessId, inputFolderPath, outputFolderPath } = await request.json();

    if (!businessId || !inputFolderPath || !outputFolderPath) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Get business to retrieve Google Drive tokens
    const business = await BusinessService.getBusiness(businessId);
    if (!business.googleDrive?.accessToken) {
      return NextResponse.json({ error: "Google Drive not connected" }, { status: 400 });
    }

    const accessToken = business.googleDrive.accessToken;

    // Create input folder
    const inputFolderResponse = await fetch('https://www.googleapis.com/drive/v3/files', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: inputFolderPath.split('/').pop(),
        mimeType: 'application/vnd.google-apps.folder',
      }),
    });

    if (!inputFolderResponse.ok) {
      throw new Error('Failed to create input folder');
    }

    const inputFolder = await inputFolderResponse.json();

    // Create output folder
    const outputFolderResponse = await fetch('https://www.googleapis.com/drive/v3/files', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: outputFolderPath.split('/').pop(),
        mimeType: 'application/vnd.google-apps.folder',
      }),
    });

    if (!outputFolderResponse.ok) {
      throw new Error('Failed to create output folder');
    }

    const outputFolder = await outputFolderResponse.json();

    // Update business with folder IDs
    await BusinessService.updateGoogleDriveConfig(businessId, {
      ...business.googleDrive,
      inputFolderPath,
      outputFolderPath,
      inputFolderId: inputFolder.id,
      outputFolderId: outputFolder.id,
    });

    return NextResponse.json({
      inputFolder: {
        id: inputFolder.id,
        name: inputFolder.name,
        webViewLink: `https://drive.google.com/drive/folders/${inputFolder.id}`,
      },
      outputFolder: {
        id: outputFolder.id,
        name: outputFolder.name,
        webViewLink: `https://drive.google.com/drive/folders/${outputFolder.id}`,
      },
    });
  } catch (error) {
    console.error("Error creating Google Drive folders:", error);
    return NextResponse.json(
      { error: "Failed to create folders" },
      { status: 500 }
    );
  }
}